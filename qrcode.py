from imutils.video import VideoStream
from pyzbar import pyzbar
import argparse
import numpy as np
import imutils
import time
import cv2

import asyncio
from pyppeteer import launch
from pyppeteer_stealth import stealth


async def print_res(name):
    if name.find("https://www.gosuslugi.ru/") == -1:
        return
    matx = np.zeros((500, 800))
    font = cv2.FONT_HERSHEY_SIMPLEX
    bottomLeftCornerOfText = (400, 250)
    fontScale = 1
    fontColor = (255, 255, 255)
    thickness = 1
    lineType = 2
    cv2.putText(matx, 'Wait...',
                bottomLeftCornerOfText,
                font,
                fontScale,
                fontColor,
                thickness,
                lineType)

    cv2.imshow(name, matx)
    browser = await launch(headless=True)
    page = await browser.newPage()

    await stealth(page)  # <-- Here

    await page.goto(name)
    await page.screenshot({'path': 'example.png'})
    content = await page.evaluate('document.body.textContent', force_expr=True)
    if content.find("Действителен") != -1:
        matx = np.zeros((500, 800))
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (300, 250)
        fontScale = 1
        fontColor = (255, 255, 255)
        thickness = 1
        lineType = 2
        cv2.putText(matx, "The certificate is valid",
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)
        cv2.imshow(name, matx)
    else:
        matx = np.zeros((500, 800))
        font = cv2.FONT_HERSHEY_SIMPLEX
        bottomLeftCornerOfText = (300, 250)
        fontScale = 1
        fontColor = (255, 255, 255)
        thickness = 1
        lineType = 2
        cv2.putText(matx, "The certificate is invalid",
                    bottomLeftCornerOfText,
                    font,
                    fontScale,
                    fontColor,
                    thickness,
                    lineType)

        cv2.imshow(name, matx)
    await browser.close()


# construct the argument parser and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-o", "--output", type=str, default="barcodes.csv",
                help="path to output CSV file containing barcodes")
args = vars(ap.parse_args())

# initialize the video stream and allow the camera sensor to warm up
print("[INFO] starting video stream...")
vs = VideoStream(src=0).start()
# vs = VideoStream(usePiCamera=True).start()
time.sleep(2.0)

# open the output CSV file for writing and initialize the set of
# barcodes found thus far
found = set()

# loop over the frames from the video stream
while True:
    # grab the frame from the threaded video stream and resize it to
    # have a maximum width of 400 pixels
    frame = vs.read()
    frame = imutils.resize(frame, width=400)

    # find the barcodes in the frame and decode each of the barcodes
    barcodes = pyzbar.decode(frame)

    # loop over the detected barcodes
    for barcode in barcodes:
        # extract the bounding box location of the barcode and draw
        # the bounding box surrounding the barcode on the image
        (x, y, w, h) = barcode.rect
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

        # the barcode data is a bytes object so if we want to draw it
        # on our output image we need to convert it to a string first
        barcodeData = barcode.data.decode("utf-8")
        barcodeType = barcode.type

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)
        cv2.putText(frame, text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

        # if the barcode text is currently not in our CSV file, write
        # the timestamp + barcode to disk and update the set
        if barcodeData not in found:
            print(barcodeData)
            found.add(barcodeData)
            asyncio.run(print_res(barcodeData))

    # show the output frame
    cv2.imshow("Scanner", frame)
    key = cv2.waitKey(1) & 0xFF

    # if the `q` key was pressed, break from the loop
    if key == ord("q"):
        break

print("[INFO] cleaning up...")
cv2.destroyAllWindows()
vs.stop()
