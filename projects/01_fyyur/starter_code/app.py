#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from models import Show, Venue, Artist
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
    date = dateutil.parser.parse(value)
  else:
    date = value
  if format == 'full':
    format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  venues = Venue.query.all()
  places = Venue.query.distinct(Venue.city,Venue.state).all()
  data = []

  for place in places: 
    data.append({
      "city": place.city,
      "state": place.state,
      "venues": [{
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len([show for show in venue.shows if show.start_time >= datetime.now()]),
      } for venue in venues if venue.city == place.city and venue.state == place.state]
    })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term','')
  search = f'%{search_term}%' 
  results = Venue.query.filter(Venue.name.ilike(search)).all()
  response={
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len([show for show in result.shows if show.start_time >= datetime.now()]),
    } for result in results]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  result = Venue.query.filter(Venue.id == venue_id).first()

  past_shows_query = Show.query.join(Venue).filter(Show.venue_id==Venue.id).filter(Show.start_time < datetime.now()).all()

  upcoming_shows_query = Show.query.join(Venue).filter(Show.venue_id==Venue.id).filter(Show.start_time >= datetime.now()).all()

  past_shows = [{
    "artist_id": show.artist_id,
    "artist_name": Artist.query.filter(Artist.id==show.artist_id).first().name,
    "artist_image_link": Artist.query.filter(Artist.id==show.artist_id).first().image_link,
    "start_time": show.start_time
  } for show in past_shows_query]

  upcoming_shows = [{
    "artist_id": show.artist_id,
    "artist_name": Artist.query.filter(Artist.id==show.artist_id).first().name,
    "artist_image_link": Artist.query.filter(Artist.id==show.artist_id).first().image_link,
    "start_time": show.start_time
  } for show in upcoming_shows_query]

  data={
    "id": result.id,
    "name": result.name,
    "genres": result.genres,
    "address": result.address,
    "city": result.city,
    "state": result.state,
    "phone": result.phone,
    "website": result.website_link,
    "facebook_link": result.facebook_link,
    "seeking_talent": result.seeking_talent,
    "seeking_description": result.seeking_description,
    "image_link": result.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # Getting form data
  form = VenueForm(request.form)
  try:
    seeking_talent=False
    if 'seeking_talent' in form: 
      seeking_talent = form['seeking_talent'] =='y'
    new_venue = Venue(
      name=form['name'].data,
      city=form['city'].data,
      state=form['state'].data,
      phone=form['phone'].data,
      address=form['address'].data,
      genres=form['genres'].data,
      facebook_link=form['facebook_link'].data,
      image_link=form['image_link'].data,
      website_link=form['website_link'].data,
      seeking_talent=seeking_talent,
      seeking_description = form['seeking_description'].data
    )

    print(type(form['genres'].data))
    db.session.add(new_venue)
    db.session.commit()
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  
  finally: 
    db.session.close()
  
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/delete', methods=['POST'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try: 
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
    flash('Venue was successfully deleted!')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('An error occurred. Venue could not be deleted.')
  
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database

  artists = Artist.query.all()
  data = []

  for artist in artists: 
    data.append({
      'id': artist.id,
      'name': artist.name
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term','')
  search = f'%{search_term}%' 
  results = Artist.query.filter(Artist.name.ilike(search)).all()
  response={
    "count": len(results),
    "data": [{
      "id": result.id,
      "name": result.name,
      "num_upcoming_shows": len([show for show in result.shows if show.start_time >= datetime.now()])
    } for result in results]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  result = Artist.query.filter(Artist.id == artist_id).first()

  past_shows_query = Show.query.join(Artist).filter(Show.artist_id==Artist.id).filter(Show.start_time < datetime.now()).all()

  upcoming_shows_query = Show.query.join(Artist).filter(Show.artist_id==Artist.id).filter(Show.start_time >= datetime.now()).all()

  past_shows = [{
    "venue_id": show.venue_id,
    "venue_name": Venue.query.filter(Venue.id==show.venue_id).first().name,
    "venue_image_link": Venue.query.filter(Venue.id==show.venue_id).first().image_link,
    "start_time": show.start_time
  } for show in past_shows_query]

  upcoming_shows = [{
    "venue_id": show.venue_id,
    "venue_name": Venue.query.filter(Venue.id==show.venue_id).first().name,
    "venue_image_link": Venue.query.filter(Venue.id==show.venue_id).first().image_link,
    "start_time": show.start_time
  } for show in upcoming_shows_query]

  data={
    "id": result.id,
    "name": result.name,
    "genres": result.genres,
    "city": result.city,
    "state": result.state,
    "phone": result.phone,
    "website": result.website_link,
    "facebook_link": result.facebook_link,
    "seeking_venue": result.seeking_venue,
    "seeking_description": result.seeking_description,
    "image_link": result.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows),
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  form = ArtistForm(obj=artist)
  
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  form = ArtistForm(request.form)
  try: 
    new_artist = {
      "name": form.name.data,
      "genres": form.genres.data,
      "city": form.city.data,
      "state": form.state.data,
      "phone": form.phone.data,
      "website": form.website_link.data,
      "facebook_link": form.facebook_link.data,
      "seeking_venue": form.seeking_venue.data,
      "seeking_description": form.seeking_description.data,
      "image_link": form.image_link.data,
    }
    old_artist = Artist.query.get(artist_id)

    old_artist.name = new_artist['name']
    old_artist.genres = new_artist['genres']
    old_artist.city = new_artist['city']
    old_artist.state = new_artist['state']
    old_artist.phone = new_artist['phone']
    old_artist.website_link = new_artist['website']
    old_artist.facebook_link = new_artist['facebook_link']
    old_artist.seeking_venue = new_artist['seeking_venue']
    old_artist.seeking_description = new_artist['seeking_description']
    old_artist.image_link = new_artist['image_link']
    
    db.session.commit()

    flash('Artist successfully edited')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('Something went wrong! Artist was not edited')

  finally: 
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artists/<int:artist_id>/delete', methods=['POST'])
def delete_artist(artist_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try: 
    artist = Artist.query.get(artist_id)
    db.session.delete(artist)
    db.session.commit()
    flash('Artist was successfully deleted!')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist could not be deleted.')
  
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue=Venue.query.get(venue_id)
  form = VenueForm(obj=venue)
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  form = VenueForm(request.form)
  try: 
    new_venue = {
      "name": form.name.data,
      "genres": form.genres.data,
      "city": form.city.data,
      "address": form.address.data,
      "state": form.state.data,
      "phone": form.phone.data,
      "website": form.website_link.data,
      "facebook_link": form.facebook_link.data,
      "seeking_talent": form.seeking_talent.data,
      "seeking_description": form.seeking_description.data,
      "image_link": form.image_link.data,
    }
    old_venue = Venue.query.get(venue_id)

    old_venue.name = new_venue['name']
    old_venue.genres = new_venue['genres']
    old_venue.city = new_venue['city']
    old_venue.address = new_venue['address']
    old_venue.state = new_venue['state']
    old_venue.phone = new_venue['phone']
    old_venue.website_link = new_venue['website']
    old_venue.facebook_link = new_venue['facebook_link']
    old_venue.seeking_talent = new_venue['seeking_talent']
    old_venue.seeking_description = new_venue['seeking_description']
    old_venue.image_link = new_venue['image_link']
    
    db.session.commit()

    flash('Venue successfully edited')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('Something went wrong! Artist was not edited')

  finally: 
    db.session.close()

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  form = ArtistForm(request.form)
  try:
    seeking_venue=False
    if 'seeking_venue' in form: 
      seeking_talent = form['seeking_venue'] =='y'
    new_artist = Artist(
      name=form['name'].data,
      city=form['city'].data,
      state=form['state'].data,
      phone=form['phone'].data,
      genres=form['genres'].data,
      facebook_link=form['facebook_link'].data,
      image_link=form['image_link'].data,
      website_link=form['website_link'].data,
      seeking_venue=seeking_venue,
      seeking_description = form['seeking_description'].data
    )

    db.session.add(new_artist)
    db.session.commit()
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  
  finally: 
    db.session.close()

  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.

  shows = Show.query.all()
  data = [{
   'venue_id': show.venue_id,
   'venue_name': Venue.query.filter(Venue.id == show.venue_id).first().name,
   'artist_id':  show.artist_id,
   'artist_name':  Artist.query.filter(Artist.id == show.artist_id).first().name,
   'artist_image_link': Artist.query.filter(Artist.id == show.artist_id).first().image_link,
   'start_time': show.start_time
  } for show in shows]
  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  form = ShowForm(request.form)

  try: 
    new_show = Show(
      artist_id=form['artist_id'].data,
      venue_id=form['venue_id'].data,
      start_time=form['start_time'].data
    )

    db.session.add(new_show)
    db.session.commit()
    flash('Show was successfully listed!')

  except exc.SQLAlchemyError as e: 
    print(e)
    db.session.rollback()
    flash('Show was not created')
  
  finally: 
    db.session.close()
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
