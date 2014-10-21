Post IDs are 5 to 8-digit numbers expressed in [NewBase60](http://tantek.pbworks.com/w/page/19402946/NewBase60). The number of digits is determined by the posting app's data resolution (which is saved in the app post for the app in question). The data resolution determines the speed with which an app is expected to post:

  * 5 digits = minute resolution
  * 6 digits = second resolution
  * 7 digits = 60 Hz resolution
  * 8 digits = 3600 Hz resolution

The resolution of an app also determines how long it should wait to retry an HTTP request in case of an error. 

During the authentication process, the server pulls up the credentials for the app, along with its stated resolution, and assigns an ID based on that. Apps do not assign IDs themselves in order to avoid time-stamp conflicts.