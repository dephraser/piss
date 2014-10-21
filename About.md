## What PISS isn't
PISS isn't about storing everything you have ever made ever. It's about storing everything that you *want* to save. Do you really want to save every Twitter @reply and Facebook comment on your personal website? Probably not. The same is true for every picture you take with your phone or any number of pieces of data that you generate every day simply by existing. Most of that stuff is *meant* to be ephemeral. Despite this, there's still a pressing need to store the things that you actually want to save in a single, central place: your website. 

## Introducing PISS
At the moment, the web is pulling us in many different directions at once. You put your statuses on Twitter, your rants on Facebook, your photos on Flickr, your code snippets on Gist, your scrobbles on Last.fm... In order to get a good picture of the kind of person that you are, people have to visit several different websites. What's more, we sometimes don't update our personal websites for months at a time because they weren't designed to deal with the kind of data that we generate on a daily basis. 

To combat this problem, PISS was designed with these ideas in mind:

  * If you want to save or share something on the internet, a record of that intention should live on your website
  * A visitor to your website should have a good idea of the kind of person you are without having to visit a silo like Twitter or Facebook
  * Third-party silos are not long-term storage solutions
 
There's a growing concern among the Internet's foremost thinkers that we are 'siloing' our lives into data stores that we can't control. Projects like [IndieWebCamp](http://indiewebcamp.com/) were created to address that concern. The idea is that the web should shift back to independent websites instead of depending on the walled gardens. The primary goal is to have control and ownership over your personal data.

## Structure
PISS takes a lot of ideas about how to structure its data from the [Tent protocol](https://tent.io). At some point in the future I hope to switch PISS to a Tent backend, but the protocol is in such a state of flux at the moment that I thought it best to construct the app first and backport it to Tent later.

In PISS, as in Tent, everything is a post. However, posts can have different types and the post type is what determines how a particular app will manipulate the data. Post types could include status posts, blog posts, photos, code snippets, scrobbles, links, etc. The PISS server will save the post type and its content, then PISS client applications can consume that data however they see fit.

Besides public posts that you want to display on your website, PISS also has the ability to save private posts and other people's posts (which I lovingly call OPP). While private posts don't seem like they have a place on your website, remember that one of the goals of PISS is to hold everything that you want to save. Sometimes you want to save things that shouldn't necessarily be public, like task lists, reminders, calendar items, etc., so PISS allows you to specify permissions for those posts.

OPP also isn't an obvious choice for your personal website, but remember that while PISS is about saving everything that you intend to save, it isn't designed to scrape up all of your Twitter conversations or Facebook comment streams. In fact, most of the time you *don't want* to save those things. However, there are occasions when good conversations happen on the third-party silos, or you want to link to a particularly good quote on a news website, and you want to save these things: PISS allows you to specify the author so that OPP don't mix with your own posts.

Also note that an OPP should contain the content that you wish to save, not just links to it. The reason is twofold: 

  1. Links to content show an intention of sharing, and that intention was authored by you. Therefore, a link is actually a post by you, not an OPP.
  2. The intention of an OPP is to save the content for later, in case it expires (like Twitter), goes behind a paywall after a certain amount of time (like NYTimes), or otherwise disappears from the internet.

## Other Stuff
One of the main motivations for creating PISS was to keep track of the things that I create. I want to be able to save the stuff that I make, however banal, to a central place. Be it code snippets, research, sketches, photos, or what have you, I want there to be a central record of the progress of my work. 

I've found that GitHub's "Your Contributions" graphic is extremely motivational, but it only encompasses my open-source coding work. If I could integrate that idea into PISS so that it can take into account my work in several different fields, I'd be extremely happy with it.