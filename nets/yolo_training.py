import math
from random import shuffle
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from matplotlib.colors import rgb_to_hsv, hsv_to_rgb
from utils.utils import bbox_iou


def clip_by_tensor(t, t_min, t_max):
    t = t.float()

    result = (t >= t_min).float() * t + (t < t_min).float() * t_min
    result = (result <= t_max).float() * result + (result > t_max).float() * t_max
    return result


def MSELoss(pred, target):
    return (pred - target) ** 2


def BCELoss(pred, target):
    epsilon = 1e-7
    pred = clip_by_tensor(pred, epsilon, 1.0 - epsilon)
    output = -target * torch.log(pred) - (1.0 - target) * torch.log(1.0 - pred)
    return output


class YOLOLoss(nn.Module):
    def __init__(self, anchors, num_classes, img_size):
        super(YOLOLoss, self).__init__()
        self.anchors = anchors
        self.num_anchors = len(anchors)
        self.num_classes = num_classes
        self.bbox_attrs = 5 + num_classes
        self.img_size = img_size

        self.ignore_threshold = 0.5
        self.lambda_xy = 1.0
        self.lambda_wh = 1.0
        self.lambda_conf = 1.0
        self.lambda_cls = 1.0

    def forward(self, input, targets=None):
        # 一共多少张图片
        bs = input.size(0)
        # 特征层的高
        in_h = input.size(2)
        # 特征层的宽
        in_w = input.size(3)
        # 计算步长
        stride_h = self.img_size[1] / in_h
        stride_w = self.img_size[0] / in_w
        # 把先验框的尺寸调整成特征层大小的形式
        scaled_anchors = [(a_w / stride_w, a_h / stride_h) for a_w, a_h in self.anchors]
        # reshape
        prediction = input.view(bs, int(self.num_anchors / 3),
                                self.bbox_attrs, in_h, in_w).permute(0, 1, 3, 4, 2).contiguous()

        # 对prediction预测进行调整
        x = torch.sigmoid(prediction[..., 0])  # Center x
        y = torch.sigmoid(prediction[..., 1])  # Center y
        w = prediction[..., 2]  # Width
        h = prediction[..., 3]  # Height
        conf = torch.sigmoid(prediction[..., 4])  # Conf
        pred_cls = torch.sigmoid(prediction[..., 5:])  # Cls pred.

        # 找到哪些先验框内部包含物体
        mask, noobj_mask, tx, ty, tw, th, tconf, tcls, box_loss_scale_x, box_loss_scale_y = \
            self.get_target(targets, scaled_anchors,
                            in_w, in_h,
                            self.ignore_threshold)

        noobj_mask = self.get_ignore(prediction, targets, scaled_anchors, in_w, in_h, noobj_mask)

        box_loss_scale_x = (2 - box_loss_scale_x).cuda()
        box_loss_scale_y = (2 - box_loss_scale_y).cuda()
        box_loss_scale = box_loss_scale_x * box_loss_scale_y
        mask, noobj_mask = mask.cuda(), noobj_mask.cuda()
        tx, ty, tw, th = tx.cuda(), ty.cuda(), tw.cuda(), th.cuda()
        tconf, tcls = tconf.cuda(), tcls.cuda()
        #  losses.
        loss_x = torch.sum(BCELoss(x, tx) / bs * box_loss_scale * mask)
        loss_y = torch.sum(BCELoss(y, ty) / bs * box_loss_scale * mask)
        loss_w = torch.sum(MSELoss(w, tw) / bs * 0.5 * box_loss_scale * mask)
        loss_h = torch.sum(MSELoss(h, th) / bs * 0.5 * box_loss_scale * mask)

        loss_conf = torch.sum(BCELoss(conf, mask) * mask / bs) + \
                    torch.sum(BCELoss(conf, mask) * noobj_mask / bs)

        loss_cls = torch.sum(BCELoss(pred_cls[mask == 1], tcls[mask == 1]) / bs)

        loss = loss_x * self.lambda_xy + loss_y * self.lambda_xy + \
               loss_w * self.lambda_wh + loss_h * self.lambda_wh + \
               loss_conf * self.lambda_conf + loss_cls * self.lambda_cls
        # print(loss, loss_x.item() + loss_y.item(), loss_w.item() + loss_h.item(), 
        #         loss_conf.item(), loss_cls.item(), \
        #         torch.sum(mask),torch.sum(noobj_mask))
        return loss, loss_x.item(), loss_y.item(), loss_w.item(), \
               loss_h.item(), loss_conf.item(), loss_cls.item()

    def get_target(self, target, anchors, in_w, in_h, ignore_threshold):
        # 计算一共有多少张图片
        bs = len(target)
        # 获得先验框
        anchor_index = [[0, 1, 2], [3, 4, 5], [6, 7, 8]][[13, 26, 52].index(in_w)]
        subtract_index = [0, 3, 6][[13, 26, 52].index(in_w)]
        # 创建全是0或者全是1的阵列
        mask = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        noobj_mask = torch.ones(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)

        tx = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        ty = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        tw = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        th = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        tconf = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        tcls = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, self.num_classes, requires_grad=False)

        box_loss_scale_x = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        box_loss_scale_y = torch.zeros(bs, int(self.num_anchors / 3), in_h, in_w, requires_grad=False)
        for b in range(bs):
            for t in range(target[b].shape[0]):
                # 计算出在特征层上的点位
                gx = target[b][t, 0] * in_w
                gy = target[b][t, 1] * in_h
                gw = target[b][t, 2] * in_w
                gh = target[b][t, 3] * in_h

                # 计算出属于哪个网格
                gi = int(gx)
                gj = int(gy)

                # 计算真实框的位置
                gt_box = torch.FloatTensor(np.array([0, 0, gw, gh])).unsqueeze(0)

                # 计算出所有先验框的位置
                anchor_shapes = torch.FloatTensor(np.concatenate((np.zeros((self.num_anchors, 2)),
                                                                  np.array(anchors)), 1))
                # 计算重合程度
                anch_ious = bbox_iou(gt_box, anchor_shapes)

                # Find the best matching anchor box
                best_n = np.argmax(anch_ious)
                if best_n not in anchor_index:
                    continue
                # Masks
                if (gj < in_h) and (gi < in_w):
                    best_n = best_n - subtract_index
                    # 判定哪些先验框内部真实的存在物体
                    noobj_mask[b, best_n, gj, gi] = 0
                    mask[b, best_n, gj, gi] = 1
                    # 计算先验框中心调整参数
                    tx[b, best_n, gj, gi] = gx - gi
                    ty[b, best_n, gj, gi] = gy - gj
                    # 计算先验框宽高调整参数
                    tw[b, best_n, gj, gi] = math.log(gw / anchors[best_n + subtract_index][0])
                    th[b, best_n, gj, gi] = math.log(gh / anchors[best_n + subtract_index][1])
                    # 用于获得xywh的比例
                    box_loss_scale_x[b, best_n, gj, gi] = target[b][t, 2]
                    box_loss_scale_y[b, best_n, gj, gi] = target[b][t, 3]
                    # 物体置信度
                    tconf[b, best_n, gj, gi] = 1
                    # 种类
                    tcls[b, best_n, gj, gi, int(target[b][t, 4])] = 1
                else:
                    print('Step {0} out of bound'.format(b))
                    print('gj: {0}, height: {1} | gi: {2}, width: {3}'.format(gj, in_h, gi, in_w))
                    continue

        return mask, noobj_mask, tx, ty, tw, th, tconf, tcls, box_loss_scale_x, box_loss_scale_y

    def get_ignore(self, prediction, target, scaled_anchors, in_w, in_h, noobj_mask):
        bs = len(target)
        anchor_index = [[0, 1, 2], [3, 4, 5], [6, 7, 8]][[13, 26, 52].index(in_w)]
        scaled_anchors = np.array(scaled_anchors)[anchor_index]
        # print(scaled_anchors)
        # 先验框的中心位置的调整参数
        x_all = torch.sigmoid(prediction[..., 0])
        y_all = torch.sigmoid(prediction[..., 1])
        # 先验框的宽高调整参数
        w_all = prediction[..., 2]  # Width
        h_all = prediction[..., 3]  # Height
        for i in range(bs):
            x = x_all[i]
            y = y_all[i]
            w = w_all[i]
            h = h_all[i]

            FloatTensor = torch.cuda.FloatTensor if x.is_cuda else torch.FloatTensor
            LongTensor = torch.cuda.LongTensor if x.is_cuda else torch.LongTensor

            # 生成网格，先验框中心，网格左上角
            grid_x = torch.linspace(0, in_w - 1, in_w).repeat(in_w, 1).repeat(
                int(self.num_anchors / 3), 1, 1).view(x.shape).type(FloatTensor)
            grid_y = torch.linspace(0, in_h - 1, in_h).repeat(in_h, 1).t().repeat(
                int(self.num_anchors / 3), 1, 1).view(y.shape).type(FloatTensor)

            # 生成先验框的宽高
            anchor_w = FloatTensor(scaled_anchors).index_select(1, LongTensor([0]))
            anchor_h = FloatTensor(scaled_anchors).index_select(1, LongTensor([1]))

            anchor_w = anchor_w.repeat(1, 1, in_h * in_w).view(w.shape)
            anchor_h = anchor_h.repeat(1, 1, in_h * in_w).view(h.shape)

            # 计算调整后的先验框中心与宽高
            pred_boxes = torch.FloatTensor(prediction[0][..., :4].shape)
            pred_boxes[..., 0] = x.data + grid_x
            pred_boxes[..., 1] = y.data + grid_y
            pred_boxes[..., 2] = torch.exp(w.data) * anchor_w
            pred_boxes[..., 3] = torch.exp(h.data) * anchor_h

            pred_boxes = pred_boxes.view(-1, 4)

            for t in range(target[i].shape[0]):
                gx = target[i][t, 0] * in_w
                gy = target[i][t, 1] * in_h
                gw = target[i][t, 2] * in_w
                gh = target[i][t, 3] * in_h
                gt_box = torch.FloatTensor(np.array([gx, gy, gw, gh])).unsqueeze(0)

                anch_ious = bbox_iou(gt_box, pred_boxes, x1y1x2y2=False)
                anch_ious = anch_ious.view(x.size())
                noobj_mask[i][anch_ious > self.ignore_threshold] = 0
                # print(torch.max(anch_ious))
        return noobj_mask


def rand(a=0, b=1):
    return np.random.rand() * (b - a) + a


class Generator(object):
    def __init__(self, batch_size,
                 train_lines, image_size,
                 ):

        self.batch_size = batch_size
        self.train_lines = train_lines
        self.train_batches = len(train_lines)
        self.image_size = image_size

    def get_random_data(self, annotation_line, input_shape, random=True, jitter=.1, hue=.1, sat=1.3, val=1.3,
                        proc_img=True):
        '''r实时数据增强的随机预处理'''
        line = annotation_line.split()
        image = Image.open(line[0])
        iw, ih = image.size
        h, w = input_shape
        box = np.array([np.array(list(map(int, box.split(',')))) for box in line[1:]])

        # resize image
        new_ar = w / h * rand(1 - jitter, 1 + jitter) / rand(1 - jitter, 1 + jitter)
        scale = rand(.25, 2)
        if new_ar < 1:
            nh = int(scale * h)
            nw = int(nh * new_ar)
        else:
            nw = int(scale * w)
            nh = int(nw / new_ar)
        image = image.resize((nw, nh), Image.BICUBIC)

        # place image
        dx = int(rand(0, w - nw))
        dy = int(rand(0, h - nh))
        new_image = Image.new('RGB', (w, h), (128, 128, 128))
        new_image.paste(image, (dx, dy))
        image = new_image

        # flip image or not
        flip = rand() < .5
        if flip: image = image.transpose(Image.FLIP_LEFT_RIGHT)

        # distort image
        hue = rand(-hue, hue)
        sat = rand(1, sat) if rand() < .5 else 1 / rand(1, sat)
        val = rand(1, val) if rand() < .5 else 1 / rand(1, val)
        x = rgb_to_hsv(np.array(image) / 255.)
        x[..., 0] += hue
        x[..., 0][x[..., 0] > 1] -= 1
        x[..., 0][x[..., 0] < 0] += 1
        x[..., 1] *= sat
        x[..., 2] *= val
        x[x > 1] = 1
        x[x < 0] = 0
        image_data = hsv_to_rgb(x) * 255  # numpy array, 0 to 1

        # correct boxes
        box_data = np.zeros((len(box), 5))
        if len(box) > 0:
            np.random.shuffle(box)
            box[:, [0, 2]] = box[:, [0, 2]] * nw / iw + dx
            box[:, [1, 3]] = box[:, [1, 3]] * nh / ih + dy
            if flip: box[:, [0, 2]] = w - box[:, [2, 0]]
            box[:, 0:2][box[:, 0:2] < 0] = 0
            box[:, 2][box[:, 2] > w] = w
            box[:, 3][box[:, 3] > h] = h
            box_w = box[:, 2] - box[:, 0]
            box_h = box[:, 3] - box[:, 1]
            box = box[np.logical_and(box_w > 1, box_h > 1)]  # discard invalid box
            box_data = np.zeros((len(box), 5))
            box_data[:len(box)] = box
        if len(box) == 0:
            return image_data, []

        if (box_data[:, :4] > 0).any():
            return image_data, box_data
        else:
            return image_data, []

    def generate(self, train=True):
        while True:
            shuffle(self.train_lines)
            lines = self.train_lines
            inputs = []
            targets = []
            for annotation_line in lines:
                img, y = self.get_random_data(annotation_line, self.image_size[0:2])

                if len(y) == 0:
                    continue
                boxes = np.array(y[:, :4], dtype=np.float32)
                boxes[:, 0] = boxes[:, 0] / self.image_size[1]
                boxes[:, 1] = boxes[:, 1] / self.image_size[0]
                boxes[:, 2] = boxes[:, 2] / self.image_size[1]
                boxes[:, 3] = boxes[:, 3] / self.image_size[0]

                boxes = np.maximum(np.minimum(boxes, 1), 0)
                boxes[:, 2] = boxes[:, 2] - boxes[:, 0]
                boxes[:, 3] = boxes[:, 3] - boxes[:, 1]

                boxes[:, 0] = boxes[:, 0] + boxes[:, 2] / 2
                boxes[:, 1] = boxes[:, 1] + boxes[:, 3] / 2
                y = np.concatenate([boxes, y[:, -1:]], axis=-1)
                img = np.array(img, dtype=np.float32)

                inputs.append(np.transpose(img / 255.0, (2, 0, 1)))
                targets.append(y)
                if len(targets) == self.batch_size:
                    tmp_inp = np.array(inputs)
                    tmp_targets = np.array(targets)
                    inputs = []
                    targets = []
                    yield tmp_inp, tmp_targets
