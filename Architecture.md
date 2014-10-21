Rather than being a monolithic application, PISS is actually made up of a collection of distinct modules.

## Data server

  * Only accept POST, PATCH, and DELETE requests from authenticated applications.
  * All POST and PATCH requests are validated to make sure they have the correct schema before being accepted. IDs and version information are generated automatically.
  * After each successful POST or PATCH the server should also send a notification to a pubsub server that a post has been added or modified.

## Display apps

  * Perform a GET request to the data server for the latest posts
  * Perform the necessary conversions to HTML, ideally marked up with Microformats2
  * Interpret short URLs and redirect them to the permalink: `sh.rt/<id>` will translate to `longurl.com/posts/<id>`
  * (Optional) Update the display document (whether an HTML page or an XML feed) in realtime in response to the pubsub server
  * (Optional) Display content based on permissions of the signed-in user.

## Authoring apps
*NOT IMPLEMENTED*

  * The post authoring app will provide fields based on the post type.
  * Posts will be written in MarkDown, but the app may allow a WYSIWYG display
  * Anything not supplied by the user but necessary for the post schema will be generated automatically to the best of the app's ability. The app should enforce some validation for known required fields.
  * The finished post is sent to the posts data server. There should be some sort of indication (like a loading graphic) that the post has been sent but a server response hasn't been received yet.
  * Once the data server accepts the post, a response is sent to the authoring app notifying that the request was completed successfully.

## Pubsub server
*NOT IMPLEMENTED*

  * Receives notifications about added or modified posts
  * Sends notifications to pubsubhubbub subscribers
  * Performs syndication to 3rd party websites
  * Interprets notifications from 3rd party websites and sends them to the API server, authoring apps, or other applications

***

## Optimization

Improving server responsiveness can be done in 2 layers:

  * Caching queries to a Redis server and letting them expire after a specified time
  * Creating static versions of app-created pages

When the server receives a request to add or change data, it should also destroy cached data as part of an event hook. When the server receives a request to retrieve data, it should also create a cache of the query.

When a request to retrieve data is received:

  * The nginx server checks if there is a frozen version of the page. 
    * If so, serve the saved page.
    * If not, the request is sent to the application
  * The application checks if the query has been cached.
    * If so, use the cached query to build the page, then save a static version.
    * If not, the query is sent to the server