#!/usr/bin/env python

# Made for python 3
import requests  # To grab webpages and download images
from fake_useragent import UserAgent  # provides headers for requests to use
import os  # To change directories
import sys  # To use arguments
import random  # Generates a random numebr for slep
from time import sleep  # Used to prevent IP timeouts by slowing down requests. optional maybe
from bs4 import BeautifulSoup  # used to parse the html returned
import shutil  # To recursively remove a directory


#Global Variables
#directory
starting_directory = os.getcwd()
download_directory = os.path.join(starting_directory, 'Comics')
# user-agent
ua = UserAgent()
header = {'User-Agent': ua.chrome}


def Setup():
    """ should be run before any other functions or statements in Main so that the download envrionment can be setup."""
    if os.path.isdir(download_directory):
        os.chdir(download_directory)
    else:
        os.makedirs(download_directory)
        os.chdir(download_directory)


def Teardown():
    """ Runs after the program finishes running to return to the state before the program was ever run."""

    os.chdir(starting_directory)


def rng(max_seconds):
    """Random number generator for time between requests to make the script appear more human.
       Returns an int"""
    random_num = random.SystemRandom().randrange(max_seconds)
    return random_num


def Page_download(page_url):
    """ Takes a url and finds the image urls, comic titles
        Then sends image urls, to Img_download for downloading."""

    page = requests.get(page_url, headers=header)
    if page.status_code == requests.codes.ok:
        page = page.content
        soup = BeautifulSoup(page, "lxml")

        # The site finishes all of their title names with a lot of little dots so we are going to remove those
        title = soup.find('h1').text
        paren_count = 0
        new_string = ''
        for char in title:
            if char == '(' or char == ')':
                paren_count += 1
                new_string += char
            else:
                if paren_count >= 2:
                    pass
                else:
                    new_string += char
        title = new_string

        img_count = 0
        img_urls = soup.find_all('img', attrs={'border': 0})
        curr_dir = os.getcwd()
        pages_dir = os.path.join(curr_dir, title)
        if os.path.isdir(pages_dir):
            redown = input("Comic Already exists, Would you like to force a re-download Y/N: ")
            if redown.lower() == 'y' or redown.lower() == 'ye' or redown.lower() == 'yes':
                # shutil deletes non empty directories unlike os.remove
                shutil.rmtree(pages_dir)
                os.makedirs(pages_dir)
                os.chdir(pages_dir)
                print("Downloading ", title)
                # creates the image_name variable by taking the title and adding page and the image count into it.
                for img_url in img_urls:
                    # There is an img tag with an alt attribute at the top of the page for a logo instead of a image
                    # Continue goes to the next iteration of the loop
                    if 'alt' in img_url.attrs:
                        continue
                    else:
                        img_count += 1
                        img_name = title + ' Page ' + str(img_count)
                        # grabs the contents of the source attribute
                        Img_download(img_url['src'], img_name)

                print("Finished Downloading ", title)
                os.chdir(curr_dir)

            elif redown.lower() == 'n' or redown.lower() == 'no':
                pass
        else:
            os.makedirs(pages_dir)
            os.chdir(pages_dir)

            print("Downloading ", title)
            for img_url in img_urls:
                if 'alt' in img_url.attrs:
                    continue
                else:
                    img_count += 1
                    img_name = title + ' Page ' + str(img_count) + '.jpg'
                    Img_download(img_url['src'], img_name)

            print("Finished Downloading ", title)
            os.chdir(curr_dir)
    else:
        print("Error occurred program halting, Error code: ", page.status_code)
        print("Error at line 50, invalid url supplied to requests.get, url: ", page_url)


def Img_download(image_url, image_name):
    """ Takes an absolute resource url and downloads the image in the url"""
    if image_url is not None:
        with open(image_name, 'wb') as image:
            image_page = requests.get(image_url, headers=header)
            if image_page.status_code == requests.codes.ok:
                image.write(image_page.content)
            else:
                print("Error at line 119")
                print("Invalid url provided for img_download: ", image_url)


def Valid_url(url):
    """ Checks to see if the url given as an argument is a valid url to download from. Returns a boolean"""
    # check the scheme if it doesn't have one it should just move on to the next checkpoint
    valid_protocols = ["http://", "https://", "http://www.", "https://www.", "www."]
    # check the host
    valid_domains = ["view-comic.com/", "viewcomic.com"]

    for schema in valid_protocols:
        if schema in url:
            protocol = schema
            url = url.split(protocol)[1]
            for valid_domain in valid_domains:
                if valid_domain in url:
                    path = url.split(valid_domain)[1]
                    return True
            # if neither domain is valid return false
            return False
    # if it makes it this far there has not been a return value yet. So it has failed to validate.
    return False


def get_page_urls(starting_page_url):
    """ Takes a starting page and checks if it contains links to comics, if so it puts the links in a list.
         Then it checks to see if there are any older pages if so it go to that page and looks for links
          before returning the list"""

    link_list = []
    start_page = requests.get(starting_page_url, headers=header)
    if start_page.status_code == requests.codes.ok:
        # the body tag's class identifies what type of page it is whether
        # single single-post or search search-results
        start_page_soup = BeautifulSoup(start_page.content, "lxml")
        body_tag = start_page_soup.find('body')
        body_tag_class = body_tag['class']
        if 'single' in body_tag_class or 'single-post' in body_tag_class:
            print("This is a single comic page not a search results page")
            print("Rerun this program with the -d option for a single page download")

        elif 'search' in body_tag_class or 'search-results' in body_tag_class:
            print("This is a search results page")
            # Grab all comic links on the page and print them to console and add them to the link_list
            # Then go to the next oldest page
            # The page breakdown is body > div(id=wrap) > section(id=primary) > div(id=content)
            # > 1 header tag or lots of divs > a(src=image_url) or div>h2.text(image name) or p
            content_div = start_page_soup.find('div', id="content")
            for tag in content_div.contents:
                if tag.name == 'div':
                    for child in tag.contents:
                        if child.name == 'a':
                            for img in child.contents:
                                image_url = img['src']

                        elif child.name == 'div':
                            for h2 in child.contents:
                                if h2.name == 'h2':
                                    for a in h2.contents:
                                        if a.name == 'a':
                                            image_name = a.text
                                            print("Image Name: ", image_name)
                                            print(" Image Url: ", image_url)
                                            # if a comic doesn't exist the status code for the thumbnail will be 404
                                            # instead of 200
                                            print("Status Code: ", requests.get(image_url, headers=header).status_code)
                                            print()
                        else:
                            print("Error line 184, tag not recognized")
                            print("Child: ", child)
                            print()
                else:
                    print("Error line 186, tag not recognized")
                    print("Tag: ", tag)
                    print()

                    # return link_list

        else:
            print('This page is not recognized as a single comic page or a comic search results page')
    else:
        print("Error at line 153")
        print("Starting Page Url provided does not exist, url: ", starting_page_url)


def Main():
    # The -d option is used for a single download
    if sys.argv[1] == '-d' or sys.argv[1] == '-download' or sys.argv[1] == '--d' or \
                    sys.argv[1] == '--download' or sys.argv[1] == '-D' or sys.argv[1] == '--D':
        if Valid_url(sys.argv[2]):
            Setup()
            Page_download(sys.argv[2])
        else:
            print("Url not Valid: ", sys.argv[2])

    # The -l option is used if you have a list of urls to download from
    elif sys.argv[1] == '-l' or sys.argv[1] == 'list' or sys.argv[1] == '--l' or sys.argv[1] == '--list' \
            or sys.argv[1] == '-L' or sys.argv[1] == '--L':
        try:
            list_file = open(sys.argv[2], 'r')
            Setup()

            for url in list_file:
                # possible 20 second sleep in between getting urls rng = random number generator
                sleep(rng(5))
                if Valid_url(url):
                    Page_download(url)
                    # possible minute and a half between downloads
                else:
                    print("Url not Valid: ", url)
            list_file.close()
        except IOError:
            print("File does not appear to exist.")

    elif sys.argv[1] == '-h' or sys.argv[1] == '-help' or sys.argv[1] == '--h' or sys.argv[1] == '--help' \
            or sys.argv[1] == '-H' or sys.argv[1] == '--H':
        print("\nUsage: python comic-dl {option} {url/file} \
         \n\n  Descriptions:\
         \n    -d downloads the comic at the url\
         \n    -l downloads every comic in the list file that is specified\
         \n    -r continuously downloads from a search results url until no comics can be found\
         \n  Examples:\
         \n    python comic-dl -d url\
         \n    python comic-dl -d http://view-comic.com/the-totally-awesome-hulk-020-2017/ \
         \n    python comic-dl -l filename (containing list of urls use absolute paths) \
         \n    python comic-dl -l urllist.txt \
         \n    python comic-dl -l /home/j/Desktop/urllist.txt \
         \n    python comic-dl -r http://view-comic.com/?s=nightwing")

    elif sys.argv[1] == '-r' or sys.argv[1] == '-recursive' or sys.argv[1] == '--r' or sys.argv[1] == '--recursive' \
            or sys.argv[1] == '-R' or sys.argv[1] == '--R':
        if Valid_url(sys.argv[2]):
            Setup()
            get_page_urls(sys.argv[2])
        else:
            print("Url not Valid: ", sys.argv[2])

    Teardown()


if __name__ == "__main__":
    Main()
