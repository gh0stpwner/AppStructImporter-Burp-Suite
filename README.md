# AppStruct-Importer
AppStruct Importer is a Burp Suite extension written in python which allows users to load a list of URLs already parsed to your target sitemap or even select the app folder to be parsed and generate a list of URLs based on the files included in it.
Once you have a list, you are able to run a HTTP request to each URL and check every successful connection with your current cookie, which i recommend you to set on your Project Options. Each successful connection will then be added to your target sitemap.

**Author:** TheNerdOne

**Date:** 11/03/2020

**Base Plugin:** Burp Importer by Smeege (Unsupported)

# Original Script
The original idea came from a white box app analysis that i was doing when i found that i was missing so many files and so much parameters because i couldn't get it there with the mainstream crawling actions. So i thought what if i create a script that could create a list of URLs to import to burp? And the result was this:

![AppStruct Importer Tab](https://raw.githubusercontent.com/TheNerdOne9/AppStruct-Importer/master/Screenshots/OriginalLIST.png)

After putting this to work i thought that would be perfect if i could, instead of importing directly to sitemap, send a request through the burp proxy, where i have a couple of extensions making some analysis, and then add the URLs to sitemap. I came across this solution. Actually this solution is way better than the one working right now in the plugin as i can use multi threading async functions with python3. I still can't get this to work on burp, but I'm working on it...

![AppStruct Importer Tab](https://raw.githubusercontent.com/TheNerdOne9/AppStruct-Importer/master/Screenshots/OriginalHTTP.png)

The final thoughts about this project came when i was asking myself, should i have a separated script to make this to work? Shouldn't this be a Burp plugin? So i started reading some examples and find out a solution that was already done, by Smeege, and could fill some of my requirements. So, i started working on it and I've managed to implement some new features even though the main thing isn't still there, sending the requests thought proxy using multi threading async functions. By now it only makes a simple request, and adds it to the sitemap.


# Screenshots

