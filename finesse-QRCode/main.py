import qrcode

url = input("please enter your URL : ").strip()
file_path = r"C:\Users\umarr\OneDrive\Desktop\finesse-QRCode\QRCode.png"

qr = qrcode.QRCode()
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save(file_path)
img.show()

print("Your QR Code has been Created!")