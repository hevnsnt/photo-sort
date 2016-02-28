  photo-sort
********************************************************************************************
***** DO NOT USE THIS, it is a project in development and may RUIN all of your photos. *****

***** I will update this readme when it is ready for use                               *****
********************************************************************************************

===v0x01=======

Python script to sort photos based on EXIF data

Take a directory of a bazillion images and sort them into nice year/month folders using EXIF data (or file data if no EXIF exists)

usage: photosort.py [-h] [-v] [-t] [-m] -s SOURCEDIR -d DESTINATIONDIR

-h : help
-v : verbose mode
-t : test mode (does not actually move any files)
-m : move mode (Removes the source file, once the new file is validated (sha256))
-s : Source directory (where the files are now) [REQUIRED]
-d : Destination directory (where you want the files to go) [REQUIRED]


ex:

--before---

unsorted

	a0987asdf097sdf.jpg

	9087adka.jpg

	8ds6fsdf77fdsadf.jpg

	fjlakdjasiue.jpg


python photosort.py -m -s ./unsorted -d ./sorted -v

--after--

sorted

	2014

		08

			a0987asdf097sdf.jpg

			9087adka.jpg

	2013

		06

			8ds6fsdf77fdsadf.jpg

			fjlakdjasiue.jpg
