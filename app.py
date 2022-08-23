#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import collections
import collections.abc
collections.Callable = collections.abc.Callable
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config 
import sys
from models import app, db, Venue, Artist, Show


app.config.from_object('config')
moment = Moment(app)
db.init_app(app)
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app.config['TEMPLATES_AUTO_RELOAD'] = True




# TODO: connect to a local postgresql database
#app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#db.create_all()

#---------------------------------#
#Filters.
#---------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#---------------------------------#
# Controllers.
#---------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#---------------------------------#
#  Venues
#---------------------------------#

@app.route('/venues')
def venues():
    data = []
    venues = Venue.query.all()
    
    locations = set()
    
    #adds city/state
    for venue in venues:
      locations.add((venue.city, venue.state))
      
    for location in locations:
        data.append({
      "city": location[0],
      "state": location[1],
      "venues": []
    })
          
    for venue in venues:
      num_upcoming_shows = 0

      shows = Show.query.filter_by(venue_id=venue.id).all()
      current_date = datetime.now()
      
      for show in shows:
        if show.start_time > current_date:
          num_upcoming_shows += 1
          
      for venue_location in data:
        if venue.state == venue_location['state'] and venue.city == venue_location['city']:
            venue_location['venues'].append({
              'id': venue.id,
              'name': venue.name,
              'num_upcoming_shows': num_upcoming_shows
            })
    return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    result = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
    
    response = {
      "count": result.count(),
      "data": result
    }
    
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

#show a specific venue
@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    shows = Show.query.filter_by(venue_id=venue_id).all()
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    #past_shows.detail =db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time < datetime.now()).all()
    upcoming_shows_detail = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>= datetime.now()).all()  
  
  
    for show in upcoming_shows_detail:
      data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
          }
      if show.start_time > current_time:
        upcoming_shows.append(data)
      else:
        past_shows.append(data)

    data={
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description":venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_venue.html', venue=venue)


#  Create Venue
@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission(): 
  form = VenueForm(request.form)

  venue = Venue(
    name = form.name.data,
    genres = form.genres.data,
    address = form.address.data,
    city = form.city.data,
    state = form.state.data,
    phone = form.phone.data,
    image_link = form.image_link.data,
    facebook_link = form.facebook_link.data,
    website = form.website.data, 
    seeking_talent = form.seeking_talent.data,
    seeking_description = form.seeking_description.data,
  )
  try:
      db.session.add(venue)
      db.session.commit()
      # on successful db insert, flash success
      flash('Venue ' + form.name.data + ' was successfully listed!')
  except:
      flash('An error occurred. Venue ' + form.name.data + ' could not be added.')
  finally:
      db.session.close()
  return render_template('pages/home.html')


#delete a venue 
@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        
        db.session.delete(venue)
        db.session.commit()
        
        flash(venue_name + ' was deleted')
        
    except:
        flash('An error occurred and ' + venue_name + ' was not deleted')
        db.session.rollback()
    finally:
        db.session.close()
    return redirect(url_for('index'))
  
@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = Venue.query.get(venue_id)

  if venue: 
    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.phone.data = venue.phone
    form.address.data = venue.address
    form.genres.data = venue.genres
    form.facebook_link.data = venue.facebook_link
    form.image_link.data = venue.image_link
    form.website.data = venue.website
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  error = False  
  venue = Venue.query.get(venue_id)

  try: 
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.genres = request.form.getlist('genres')
    venue.image_link = request.form['image_link']
    venue.facebook_link = request.form['facebook_link']
    venue.website = request.form['website']
    venue.seeking_talent = True if 'seeking_talent' in request.form else False 
    venue.seeking_description = request.form['seeking_description']

    db.session.commit()
  except: 
    error = True
    db.session.rollback()
    print(sys.exc_info())
  finally: 
    db.session.close()
  if error: 
    flash(f'An error occurred. Venue could not be changed.')
  if not error: 
    flash(f'Venue was successfully updated!')
  return redirect(url_for('show_venue', venue_id=venue_id))
#---------------------------------#
#  Artists
#---------------------------------#
@app.route('/artists')
def artists():
    data = []
    
    artists = Artist.query.all()
    for artist in artists:
          data.append({
            "id": artist.id,
            "name": artist.name
          })

    return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
    
    response = {
      "count": result.count(),
      "data": result
    }
    
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    shows = Show.query.filter_by(artist_id=artist_id).all()
    past_shows = []
    upcoming_shows = []
    current_time = datetime.now()
    upcoming_shows_details = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time>= datetime.now()).all()
    #past_shows_details=db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time< datetime.now()).all()
    
    for show in upcoming_shows_details:
      data = {
          'venue_id': show.venue_id,
          'venue_name': show.venue.name,
          'venue_image_link': show.venue.image_link,
          'start_time': format_datetime(str(show.start_time))
          }
          
      if show.start_time > current_time:
          upcoming_shows.append(data)      
      else:
          past_shows.append(data)

    data = {
      'id': artist.id,
      'name': artist.name,
      'genres': artist.genres,
      'city': artist.city,
      'state': artist.state,
      'phone': artist.phone,
      'facebook_link': artist.facebook_link,
      'image_link': artist.image_link,
      'past_shows': past_shows,
      'upcoming_shows': upcoming_shows,
      'past_shows_count': len(past_shows),
      'upcoming_shows_count': len(upcoming_shows)
    }
    
    
    return render_template('pages/show_artist.html', artist=data)

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  try:  
    form = ArtistForm()
    artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data,
                    phone=form.phone.data, genres=form.genres.data,
                    image_link=form.image_link.data, facebook_link=form.facebook_link.data)
    db.session.add(artist)
    db.session.commit()
    flash('The submission for Artist ' + request.form['name'] + ' was created')
  except:
    db.session.rollback()
    flash('The submission for Artist ' + request.form['name'] + ' was unable to be created')
  finally:
    db.session.close()
    
  return render_template('pages/home.html')


#edit artist 
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = Artist.query.get(artist_id)
  
  artist_data ={
    'id': artist.id,
    'name': artist.name,
    'city': artist.city,
    'state': artist.state,
    'phone': artist.phone,
    'image_link': artist.image_link,
    'genres': artist.genres,
    'facebook_link': artist.facebook_link
  
  }
      
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try: 
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    
    name = form.name.data 
    
    artist.name = name
    artist.phone = form.phone.data  
    artist.state = form.state.data
    artist.city = form.city.data  
    artist.genres = form.genres.data
    artist.image_link = form.image_link.data
    artist.facebook_link = form.facebook_link.data  
    
    db.session.commit()
    flash('The Artist ' + request.form['name'] + ' information has been successfully updated!')
  except: 
    db.session.rollback()
    flash('An Error has occurred and the update was unsuccessful')
  finally: 
    db.session.close()
  
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/artist/<int:artist_id>', methods=['DELETE'])
def delete_artist(artist_id):
      try: 
        artist = Artist.query.get(artist_id)
        artist_name = artist.name
        
        db.session.delete(artist)
        db.session.commit()
        
        flash('Artist ' + artist_name + ' . was deleted')
      except:
        flash('Artist ' + artist.name + ' was unable to be deleted')
        db.session.rollback()
        
      finally:
        db.session.close()
      return redirect(url_for('index'))

#---------------------------------#
#  Shows
#---------------------------------#

@app.route('/shows')
def shows():
    data = []
    shows = Show.query.order_by(db.desc(Show.start_time))
    for show in shows:
      data.append({
        'venue_id': show.venue_id,
        'venue_name': show.venue.name,
        'artist_id': show.artist_id,
        'artist_name': show.artist.name,
        'artist_image_link': show.artist.image_link,
        'start_time': format_datetime(str(show.start_time))
      })
  

    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():

  try:
    show = Show(artist_id=request.form['artist_id'], venue_id=request.form['venue_id'], start_time=request.form['start_time'] )
    db.session.add(show)
    db.session.commit()
    
    flash('Show was successfully listed!')
  except:
      db.session.rollback()
      flash('An error occurred. The show could not be listed')
  finally:
    db.session.close()

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

#---------------------------------#
# Launch.
#---------------------------------#


# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
