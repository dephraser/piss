Post types describe the expected schema inside the `content` property of a post. The following schemas can be used for reference and inspiration:

  * [Activity Streams](https://github.com/activitystreams/activity-schema/blob/master/activity-schema.md)
  * [Microformats2](http://microformats.org/wiki/Main_Page)
  * [Tent post types](https://tent.io/docs/post-types)

**Note:** Information about where content posts are syndicated to can be held in the `links` property of the base `post` schema, so there's no need to add that information to a post type.

## Server posts

Server posts hold information that the server uses to configure itself, information about the owner entity and entities it communicates with, etc.

  - [x] Meta
  - [x] Entity
  - [ ] Subscription
  - [ ] Delete
  - [x] Application
  - [x] Credentials
  - [ ] Group

### Meta
This is information that describes the server preferences for an entity. Since we expect to serve only a single entity from the PISS server, information in the `meta` post is saved to a `META_POST` variable in the `piss.cfg` file. 

The `meta` post also makes it possible to share public information about the main entity.

```json
{
   "name": "meta",
   "schema":
   {
       "entity":
       {
           "type": "string",
		   "required": true
       },
       "profile":
       {
           "type": "dict",
           "schema":
           {
               "name":
               {
                   "type": "string"
               },
               "description":
               {
                   "type": "string"
               },
		       "cards": {
		           "type": "list",
		           "schema": {
		               "name": {
		                   "type": "string"
		               },
		               "type": {
		                   "type": "string"
		               },
		               "datum": {
		                   "type": "string"
		               }
		           }
		       }
           }
       },
       "server":
       {
           "type": "dict",
           "required": true,
           "schema":
           {
               "version": {
				   "type": "string",
				   "required": true
               },
			   "preference": {
				   "type": "integer",
				   "required": true
			   },
			   "urls": {
				   "type": "dict",
				   "schema": {
					   "oauth_auth": {
						   "type": "string",
						   "required": true
					   },
					   "oauth_token": {
						   "type": "string",
						   "required": true
					   },
					   "types": {
						   "type": "string",
						   "required": true
					   },
					   "posts_feed": {
						   "type": "string",
						   "required": true
					   },
					   "new_post": {
						   "type": "string",
						   "required": true
					   },
					   "post": {
						   "type": "string",
						   "required": true
					   },
					   "post_attachment": {
						   "type": "string",
						   "required": true
					   },
					   "attachment": {
						   "type": "string",
						   "required": true
					   }
				   }
			   }
           }
       }
    }
}
```

### Entity
```json
{
   "name": "entity",
   "schema":
   {
       "entity":
       {
           "type": "string",
           "required": true
       },
       "profile":
       {
           "type": "dict",
           "schema":
           {
               "name":
               {
                   "type": "string"
               },
               "description":
               {
                   "type": "string"
               }
           }
       }
   }
}
```

### App
```json
{
   "name": "app",
   "schema":
   {
       "name": {
		   "type": "string",
		   "required": true
       },
       "description": {
		   "type": "string"
       },
       "url": {
		   "type": "string",
		   "required": true
       },
       "redirect_url": {
		   "type": "string",
		   "required": true
       },
       "notification_url": {
		   "type": "string"
       },
       "notification_types": {
		   "type": "list",
		   "schema": {
			   "type": "string"
		   }
       },
	   "types": {
		   "type": "dict",
		   "schema": {
			   "read": {
				   "type": "list",
				   "schema": {
					   "type": "string"
				   }
			   },
			   "write": {
				   "type": "list",
				   "schema": {
					   "type": "string"
				   }
			   }
		   }
	   }
   }
}
```

### Credentials
```json
{
   "name": "credentials",
   "schema":
   {
       "hawk_key": {
		   "type": "string",
		   "required": true
       },
       "hawk_algorithm": {
		   "type": "string",
		   "required": true
       }
   }
}
```
## Content posts

Content posts are the actual 'data' that we want to save: status posts, articles, etc.

  - [x] Note
  - [x] Card
  - [ ] Article
  - [ ] Link
  - [ ] Quote
  - [ ] Like
  - [ ] Photo
  - [ ] Repost
  - [ ] [Edit](http://indiewebcamp.com/edit)
  - [ ] Cursor

### Note
```json
{
   "name": "note",
   "schema":
   {
       "text":
       {
           "type": "string"
       },
       "location":
       {
           "type": "dict",
           "schema":
           {
               "latitude":
               {
                   "type": "string"
               },
               "altitude":
               {
                   "type": "string"
               },
               "name":
               {
                   "type": "string"
               },
               "longitude":
               {
                   "type": "string"
               }
           }
       }
   }
}
```

### Card
Used to store individual bits of contact information. Allows for per-item granularity of permissions.

```json
{
   "name": "card",
   "schema":
   {
       "cards": {
           "type": "list",
           "schema": {
               "name": {
                   "type": "string"
               },
               "type": {
                   "type": "string"
               },
               "datum": {
                   "type": "string"
               }
           }
       }
   }
}
```