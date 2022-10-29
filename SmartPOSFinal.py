from tkinter import *
import mysql.connector
from tkinter import ttk,font
from PIL import ImageTk, Image
from PIL import Image as img
import cv2
import datetime
import os
import math
from collections import defaultdict
import numpy as np
import tensorflow as tf
from tensorflow import keras
import serial
import time
from glob import glob


def load_test_img(path):
  img=cv2.imread(path)
  img=cv2.cvtColor(img,cv2.COLOR_BGR2RGB)
  img=cv2.resize(img,(100,100))
  return img

def siamOptPred(testImgOpt):  

  predListOpt={}

  inpFeatTestImg=FruVegCore.layers[-2](FruVegCore.layers[-3](np.expand_dims(testImgOpt,axis=0)))
  
  reshapedInp=np.reshape(inpFeatTestImg,(2048,))
                          

  for i in keysDB:
    predInd=siamese.layers[-1](siamese.layers[-2]([np.expand_dims(reshapedInp,axis=0),
                                              np.expand_dims(AllFeatNewDictLoaded[0][i],axis=0)
                                              ])).numpy()[0][0]

    predListOpt[i]=predInd
    keylist=list(predListOpt.keys())
    vallist=list(predListOpt.values())
    topVals=sorted(list(predListOpt.values()))[-6:][::-1]
    finallst=[]
    for i in topVals:
        finallst.append(keylist[vallist.index(i)])
    
  return finallst


""" Loading core models and data"""

FruVegCore=keras.models.load_model('checkpoint_22_05_62.h5')

siamese=tf.keras.models.load_model('siameseNew1.h5')

AllFeatNewDictLoaded=np.load('AllFeatNewDictLoaded.npy',allow_pickle=True)

keysDB=list(AllFeatNewDictLoaded[0].keys())

lst_code2item=np.load('Lst_code2item1.npy',allow_pickle=True)

data=defaultdict(int) # Bar code scanner codes

global btn_to_name_mapping# To hold name of broadCategory buttons

btn_to_name_mapping={}

global sub_btn_to_name_mapping # To hold names of subcategories of each BroadCategory item

sub_btn_to_name_mapping=defaultdict(list)

global first_single_category

first_single_category={}

global sum

sum=0 # Total of bill items!

mydb = mysql.connector.connect(
        host="127.0.0.1",
        port="3306",
        user="root",
        password="password",
        database="SmartRetail"  
        )

root = Tk()
root.title("POS Billing Application")
root.configure(bg='white')
root.iconbitmap('GTG_logo.ico')

totalHolder=Frame(root)        #Label to hold total amount value!
totalHolder.grid(row=5,column=2)

frame=Frame(root,bg="white")
frame.grid(row=5,column=7,columnspan=3)

"""
#FOR SNAPSHOT FUNCTION#
framelabel=LabelFrame(root,bg="white")
mycanvas= Canvas(framelabel,bg='white',height=300,width=300)

mycanvas.create_window((5,7), window=framelabel, anchor="se")

mycanvas.grid(row=0,column=0,columnspan=3)
framelabel.grid(row=5, column=7, columnspan=3, pady=10, rowspan=2)
########################
"""

"""Function for calculating total"""

def ttl():
     global sum
     total= Button(totalHolder, text= str(sum), font="arial 20 bold", bg="white")
     total.grid(row=5, column=2, padx=10, pady=10)

"""Weight from COM PORT"""

def weight():
    data=[]
    string=''
    flt=None
    ser = serial.Serial('COM5', 9600)
    while((string is '') or (string is None)):
        b = ser.readline()         # read a byte string
        string_n = b.decode()  # decode byte string into Unicode  
        string = string_n.rstrip()# remove \n and \r
        try:
            flt = float(string)        # convert string to float
        except:
            continue
        print("flt weight: ",flt)
    data.append(flt)    
    ser.close()   # add to the end of data list
    return data[-1]
    
    
"""Update the table"""
def updateListView(prim_key,barcode=False):
	global sum
     
     
	if(barcode is False): #FruVeg (With weight())
		try:
			billsTV.insert("", 'end', text = prim_key[0],values =( "100/kg","95 g" , "30")) #str(max(math.floor(prim_key[1])-5,0))
			destroyAllFruVegButtons()
		except:
			billsTV.insert("", 'end', text = prim_key[0],values =( "100/kg","95 g" , "30")) #str(max(math.floor(10)-5,0))
            
	else: #Barcode commodity
		try:
			billsTV.insert("", 'end', text = prim_key[0],values =( "-", prim_key[1], "30"))
		except:
			billsTV.insert("", 'end', text = prim_key[0],values =( "-", 0, "30"))
	sum =  sum+30

"""Updating current bill view"""

def writein(lst,barcode=False):
	destroyAllFruVegButtons()
	updateListView(lst,barcode)

"""Treeview"""

billsTV= ttk.Treeview(height=15, columns=('Item Name','quantity','Cost')) 

"""^^Update theme here!"""

"""Video stream"""

app = Frame(root,bg='white')
app.grid(row=0,column=7,rowspan=4,columnspan=2)
lmain = Label(app,bg='white',height=350,width=350)
lmain.grid(row=0, column= 7, rowspan=3, columnspan=2,padx=10,pady=10)
cap = cv2.VideoCapture(1)

"""Function for video streaming"""

def video_stream():
     _, frame = cap.read()
     cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
     imag = Image.fromarray(cv2image)
     imag = imag.resize((350,350),img.ANTIALIAS)
     imgtk = ImageTk.PhotoImage(image=imag)
     
     lmain.imgtk = imgtk
     lmain.configure(image=imgtk)
     lmain.after(1, video_stream)

"""Destroy buttons in FruVeg window while resetting"""
def destroyAllFruVegButtons():
	sub_btn_to_name_mapping=defaultdict(list)

	btn_to_name_mapping={}

	for i in frame.winfo_children():
		if(str(type(i)).split('.')[1][:6]=='Button'):
			i.destroy()
    
"""Displaying sub names of each Broad Category item"""
def displaySubButtons(btn_name):
    writein([os.path.basename(sub_btn_to_name_mapping[btn_name][0]),weight()])
    
"""Displaying Broad Category Images"""

def displayBroadCategory(b,imagedirs):
    
    
	print('btn_to_name_mapping: ',btn_to_name_mapping)
    
	#Delete the Buttons of the Frame() 
	for i in frame.winfo_children():
		if(str(type(i)).split('.')[1][:6]=='Button'):
			i.destroy()
    
	count=1
	RowNo=0
	ColNo=0
    
    
	#print('In displayBroadCategory , BroadNameCat:',BroadNameCat)
            
    
	for i in imagedirs[btn_to_name_mapping[b]]:
		print("in displayBroadCategory ")
		print(i)
		org_photo = Image.open(i)
		org_photo = org_photo.resize((100,100),Image.ANTIALIAS)
		photo = ImageTk.PhotoImage(org_photo)
		label = Label(image=photo)
		label.image = photo # keep a reference!
		B = Button(frame,bg='white', image = photo, borderwidth=2)
		sub_btn_to_name_mapping[str(B)].append(i)
		B.configure(command=lambda b1=B: displaySubButtons(str(b1)))
		if(count<=3):
			RowNo=0
			ColNo=count-1
		else:
			RowNo=1
			ColNo=count-4
		B.grid(row=RowNo+5, column=ColNo+7)
		count+=1

"""Display First single button"""
def FirstSingleButtonDisplay(btn_name):
	writein([first_single_category[btn_name],weight()])
        
"""Snapshot Function"""

def takeSnapshot():
	destroyAllFruVegButtons()
    
	ret,imgcv2=cap.read()
    
	dum=imgcv2
     
	imgcv2=cv2.resize(imgcv2,(100,100))

	imgcv2=cv2.cvtColor(imgcv2,cv2.COLOR_BGR2RGB)
        
	mycursor = mydb.cursor()
	itm_name=siamOptPred(imgcv2) #Model Outputs obtained!
    
	RowNo=0
	ColNo=0
    
	count=1
	
	broadflag=0 #To check if broadcategory is rendered or not
        
    
	print('itm_name: ',itm_name)
	print('itm_name_len:',len(itm_name))
    
	broadImgPaths=defaultdict(list)

    
	for v,i in enumerate(itm_name):
		print(i)
        
		broadflag=0

		if(list(i).count('.')!=0 and len(i.split(' '))>=2):
			sql=r"SELECT serialNo,Name,ImagePath,Price FROM records WHERE Name='"+i+"'"
		elif(list(i).count('.')==0 and len(i.split(' '))<=1):
			sql=r"SELECT serialNo,Name,ImagePath,Price FROM records WHERE BroadCategory='"+i+"'"
			broadflag=1

		if(len(i.split(' '))>=2 and list(i).count('.')==0):
			sql=r"SELECT serialNo,Name,ImagePath,Price FROM records WHERE BroadCategory='"+i+"'"
			print('broad here!')
			broadflag=1
		elif(len(i.split(' '))<=1 and list(i).count('.')!=0):
			sql=r"SELECT serialNo,Name,ImagePath,Price FROM records WHERE Name='"+i+"'"
			print('specific here!')
		print(sql)
            
		mycursor.execute(sql)
        
		if(count<=3):
			RowNo=0
			ColNo=count-1
		else:
			RowNo=1
			ColNo=count-4
		count+=1

            
		if(broadflag==1):
			myresult= mycursor.fetchone()
			broadImgPaths[i].append(myresult[2])
			while(myresult is not None):
				myresult= mycursor.fetchone()
				if(myresult is not None):
					broadImgPaths[i].append(myresult[2])
        
		if(broadflag==0):
			myresult= mycursor.fetchone()
			if(myresult==None):
				sql=r"SELECT serialNo,Name,ImagePath,Price FROM records WHERE Name='"+i.split('.')[0]+"'";
				mycursor.execute(sql)
				myresult= mycursor.fetchone()
                
			print("In broadflag0: ",myresult)
			org_photo = Image.open(myresult[2])
			org_photo = org_photo.resize((100,100),Image.ANTIALIAS)
			photo = ImageTk.PhotoImage(org_photo)
			label = Label(image=photo)
			label.image = photo # keep a reference!
			B = Button(frame,bg='white', image = photo, borderwidth=2)
			first_single_category[str(B)]=i
			B.configure(command=lambda b=B: writein([FirstSingleButtonDisplay(str(b)),weight()]))
			B.grid(row=RowNo+5, column=ColNo+7)
			btn_to_name_mapping[str(B)]=i
		else:
			print("In broadflag1 , path: ",broadImgPaths[i])
			B=Button(frame,bg='white', text=i, borderwidth=2)
			B.configure(command=lambda b=B : displayBroadCategory(str(b),broadImgPaths))
			B.grid(row=RowNo+5, column=ColNo+7)
			btn_to_name_mapping[str(B)]=i
        
	mycursor.close()
			
	print(broadImgPaths)
			

"""Scanner Function"""

def takeScan():
    
	ser = serial.Serial(port='COM7',
                    baudrate=9600,
                    bytesize=serial.EIGHTBITS,
                    parity=serial.PARITY_NONE,
                    timeout=2)

	while(True):
         

		val=ser.read(16).decode('utf-8').split('\r')[0]
        
		print('val: ',val)
     
		if(val==''):
			continue
         
		data[val]+=1
          
		if(data[val]>1):
         
			for item in billsTV.get_children():
				print("Inside for loop")
				if(billsTV.item(item)["text"]==lst_code2item[0][val]): #item.set(item,"#0")
					billsTV.delete(item)
					break
        
		print("Out now!")
     
		writein([lst_code2item[0][val],data[val]],barcode=True)
         
		break
	ser.close()

         
     
#==============Reset the treeview========

def rst():
     global sum
     for i in billsTV.get_children():
          billsTV.delete(i)

     sum=0
     destroyAllFruVegButtons()
     for i in totalHolder.winfo_children():
         i.destroy()
         
"""BILLING WINDOW"""

def billingwindow():
    
	Logophoto = Image.open('GTG logo Jpeg.jpg')
	Logophoto = Logophoto.resize((100,100),Image.ANTIALIAS)
	Logophoto = ImageTk.PhotoImage(Logophoto)
	label = Label(image=Logophoto)
	label.image = Logophoto # keep a reference!
	LogoButtonWidget = Button(root,bg='white',image=Logophoto)
	LogoButtonWidget.grid(row=0,column=0)
     
	titlelabel= Label(root, text="POS Billing Application", font="Times 30", bg='#ffffff')
	titlelabel.grid(row=0, column=1, columnspan=3)

	billLabel=Label(root, text="Invoice", font="Times 20", bg='#ffffff')
	billLabel.grid(row=1, column=1, padx=10 )

	billsTV.grid(row=3, column=0, columnspan=5)

	scrollBar = Scrollbar(root, orient="vertical",command=billsTV.yview)
	scrollBar.grid(row=3, column=6, sticky="NWS")
	billsTV.configure(xscrollcommand = scrollBar.set)

	billsTV.configure(yscrollcommand=scrollBar.set)

	billsTV.heading('#0',text="Item Name")
	billsTV.heading('#1',text="Rate")
	billsTV.heading('#2',text="Quantity")
	billsTV.heading('#3',text="Cost")

    
	payment_btn= Button(root,text="Total", command= ttl,width= 10, bg='green', fg='white', font='arial 20 bold', padx=10, pady=10)
	payment_btn.grid(row=4, column=1)
	Reset_btn= Button(root,text="Reset", command= rst, width= 10, bg='Red', fg='white', font='arial 20 bold', padx=10, pady=10)
	Reset_btn.grid(row=5, column=1,padx=10,pady=10)


	photo = PhotoImage(file = "Capture.png")

	label = Label(image=photo)
	photoimage = photo.subsample(2, 2)
	label.image = photoimage # keep a reference!
	buttonCapture= Button(root, image= photoimage,command= takeSnapshot, bg='white',borderwidth=0)
	buttonCapture.grid(row=4, column=7)


	scn = PhotoImage(file = "Barcode.png")
	scn_img = Label(image=scn)
	scn_img.image = scn # keep a reference!
	buttonCapture= Button(root, image= scn, command=takeScan, bg='white',borderwidth=0)
	buttonCapture.grid(row=4, column=8)

	video_stream() #video function call
      

"""Driver functions"""

if(__name__=='__main__'):
      
    billingwindow()

    root.mainloop()
