# -------------------------------------#
#       样式设计
# -------------------------------------#
class Style:
    def __init__(self):
        pass

    def style(self):
        StyleSheet = '''
        #ProgressBar {
        text-align: right;
        background-color: #2B3743;
        border-radius:8px;
        }
        #ProgressBar::chunk {
        background-color:#4CB28A;
        border-radius:3px;
        margin: 6px;
        }
        #button{
        background-color:#2B3743;
        border:none;
        }
        #button:hover{
        background-color:#1F2C35;
        border:none;
        }
        #ChooseButton1{
        background-color:#2B3743;
        font-size:16px;
        color:#4CB28A;
        border-radius:23px;
        }
        #ChooseButton2{
        background-color:#4CB28A;
        color:#2B3743;
        font-size:16px;
        border-radius:23px;
        }
        #ParamLabel{
        background-color:#4CB28A;
        font-size:16px;
        color:#1F2C35;
        border-radius:16px;
        }
        #content{
        background-color:#1F2C35;
        font-size:16px;
        color:#4CB28A;
        border-radius:16px;
        padding-left:25px;
        }
        #ResultLabel{
        background-color:#4CB28A;
        font-size:16px;
        color:#1F2C35;
        border-radius:16px;
        padding-left:27px;
        }

        #QSlider::groove{ 
        border: none; 
        background-color:#2B3743;
        border-radius:8px;
        }
        #QSlider::handle{    
        border: none;
        width: 20px;
        border-radius: 9px;
        background-color: #4CB28A;
        }
        #QSlider::add-page:horizontal  
        {   
        border-radius: 3px;  
        margin:6px;
        background-color: #1F2C35;
        }
        #QSlider::sub-page:horizontal 
        {
        border: none; 
        border-radius: 3px;
        margin: 6px 0 6px 6px;
        background-color:#4CB28A;
        }   
        '''
        return StyleSheet
