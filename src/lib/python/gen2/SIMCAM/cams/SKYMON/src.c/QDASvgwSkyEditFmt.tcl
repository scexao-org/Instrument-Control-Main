###### Skycat上に描画する図形のフォーマット指定 ######

### 座標軸の長さ ###
set LineLength(COORDINATE) 230

### 望遠鏡の大きさ ###
set OvalWidth(TELESCOPE) 16

### 星の大きさ ###
set OvalWidth(STAR) 6

### 月の大きさ ###
set OvalWidth(MOON) 20



### 座標軸の色 ###
set Color(COORDINATE) orange

### 望遠鏡(現在位置)の色 ###
set Color(TELESCOPE) green

### 望遠鏡(ターゲット)の色 ###
set Color(TELESCOPE_TAR) lightgreen

### 観測対象の星の色 ###
set Color(STAR) white
#set Color(STAR) orange
#set Color(STAR) yellow

### 観測対象の星の文字のフォント ###
set Font(STAR) -Adobe-Times-Bold-R-Normal--*-100-*-*-*-*-*-*

### 観測対象外の星の色 ###
set Color(STAR_ALL) darkgray

### 観測対象外の星の文字のフォント ###
set Font(STAR_ALL) -Adobe-Times-Medium-R-Normal--*-100-*-*-*-*-*-*

### 月の色 ###
set Color(MOON) yellow

### サンプル値の色 ###
set Color(SAMPLE) white


### 画像の中心を示すX,Y座標 ###
set CENTER(X) 250
set CENTER(Y) 250

### ELの90から0までの長さ(円の半径) ###
set CENTER(R) 200

### SkyMonitor画像の幅，高さを決定 ###
set SKYFORMATFITS(X) 500
set SKYFORMATFITS(Y) 500

### サンプル値を表示する位置（サンプル図形の左上と右下の座標） ###
### (注) SAMPLEのY座標に11を足した値が,画像の幅を超えないように設定すること ###
set SAMPLE(X1) 270
set SAMPLE(Y1) 1
set SAMPLE(X2) 499
set SAMPLE(Y2) 21

### サンプル最小値 ###
set SAMPLE(MIN) 0.0

### サンプル最大値 ###
set SAMPLE(MAX) 150.0


### 望遠鏡を表示する際の周期(ミリ秒) ###
set Wait(TELETIME) 3000

### 月と星を表示する際の周期(ミリ秒) ###
set Wait(MSTIME) 300000


### 望遠鏡の最小EL値(EL-hourグラフに表示される) ###
set EL(TEL) 15

### SkyMonitorに表示するEL座標軸の値(4本まで) ###
set EL(1) 0
set EL(2) 30
set EL(3) 60
set EL(4) 90


### 色調設定 2002.04.03 ####
### View -> Color のcolormapで上からの通番(0オリジン) ###
set Tone(Colormap) 17;	# ramp
set Tone(Intensity) 1;	# ramp

### 階調設定 2002.04.03 ###
set Gradation(LOW) 0
set Gradation(HIGH) 200

### 三日月描画パラメーター ###
### 上弦三日月 ###
set FQMoon(X1)	0
set FQMoon(Y1)	-10
set FQMoon(X2)	7
set FQMoon(Y2)	-7
set FQMoon(X3)	10
set FQMoon(Y3)	0
set FQMoon(X4)	7
set FQMoon(Y4)	7
set FQMoon(X5)	0
set FQMoon(Y5)	10
set FQMoon(X6)	5
set FQMoon(Y6)	5
set FQMoon(X7)	6
set FQMoon(Y7)	0
set FQMoon(X8)	5
set FQMoon(Y8)	-5

### 下弦三日月 ###
set LQMoon(X1)	0
set LQMoon(Y1)	-10
set LQMoon(X2)	-7
set LQMoon(Y2)	-7
set LQMoon(X3)	-10
set LQMoon(Y3)	0
set LQMoon(X4)	-7
set LQMoon(Y4)	7
set LQMoon(X5)	0
set LQMoon(Y5)	10
set LQMoon(X6)	-5
set LQMoon(Y6)	5
set LQMoon(X7)	-6
set LQMoon(Y7)	0
set LQMoon(X8)	-5
set LQMoon(Y8)	-5

