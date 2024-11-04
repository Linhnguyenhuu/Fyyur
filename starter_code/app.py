#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from sqlalchemy.orm import relationship
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import *

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
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
  data = [] 

  # get all venues
  all_same_location_venue = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).all()
    
  if all_same_location_venue is None: 
    # render with no data
    return render_template('pages/venues.html')

  for location in all_same_location_venue:
    # get all venues in same city and state
    same_location_venue = Venue.query.filter_by(city=location[0], state=location[1]).all()

    # detail info of venue
    displayed_venues = [] 
    for venue in same_location_venue:
      displayed_venues.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
      })
    
    data.append({
      "city":location[0],
      "state":location[1],
      "venues":displayed_venues,
    })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term')
  data=[]
  venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')|Venue.city.ilike(f'%{search_term}%')|Venue.state.ilike(f'%{search_term}%')).all()
  for venue in venues:
    if len(venue.shows) > 0 and Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all() is not None:
        total_show = len(Show.query.filter(Show.venue_id == venue.id).filter(Show.start_time > datetime.now()).all())
    else:
        total_show = 0
        
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": total_show,
    })
  response={
    "total": len(venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # find venue by id
  venue = Venue.query.get_or_404(venue_id)

  past_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Show.venue_id==venue_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  data = venue.__dict__
  data['past_shows'] = past_shows
  data['upcoming_shows'] = upcoming_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows_count'] = len(upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate():
      try:
          new_venue = Venue()
          form.populate_obj(new_venue)
          db.session.add(new_venue) 
          db.session.commit()
          # on successful db insert, flash success
          flash('Venue '+form.name.data+' was just inserted!')  
      except Exception as e:
          flash('An error occurred. Venue '+ form.name.data + ' could not be inserted!.')
          print(e)
          db.session.rollback()
      finally:
          db.session.close()
      return render_template('pages/home.html')
  else:
      errors = ", ".join([f"{field}: {error}" for field, errs in form.errors.items() for error in errs])
      flash(f'Please fix the following errors: {errors}')
      return render_template('forms/new_venue.html', form=form)
    

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    venue = Venue.query.filter_by(id=venue_id).first() 
    db.session.delete(venue)
    db.session.commit()
    flash('Deleted.')
  except:
    flash('Error occurred!')
    db.session.rollback()
  finally:
    db.session.close()
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = [] 

  # get all artists
  artists = Artist.query.all()
    
  if artists is None: 
    # render with no data
    return render_template('pages/artists.html')

  for artist in artists:
    # display info
    data.append({
      "id":artist.id,
      "name":artist.name,
    })

  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term')
  data=[]
  artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  for artist in artists:
    if len(artist.shows) > 0 and Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all() is not None:
        total_show = len(Show.query.filter(Show.artist_id == artist.id).filter(Show.start_time > datetime.now()).all())
    else:
        total_show = 0
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": total_show,
    })
  response={
    "count": len(artists),
    "data": data
  }

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # find artist by id
  artist = Artist.query.get_or_404(artist_id)

  past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time<datetime.now()).all()
  past_shows = []
  for show in past_shows_query:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id==artist_id).filter(Show.start_time>datetime.now()).all()
  upcoming_shows = []
  for show in upcoming_shows_query:
    upcoming_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "venue_image_link": show.venue.image_link,
      "start_time": format_datetime(str(show.start_time))
    })

  data = artist.__dict__
  data['past_shows'] = past_shows
  data['past_shows_count'] = len(past_shows)
  data['upcoming_shows'] = upcoming_shows
  data['upcoming_shows_count'] = len(upcoming_shows)
    
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()

  artist = Artist.query.get(artist_id)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  try:
          # find artist by id
          artist = Artist.query.get(artist_id)
          if artist is None: 
            flash('This artist was not exist')
            return render_template('forms/show_artist.html',form=form) 
          form.populate_obj(artist)
          db.session.add(artist) 
          db.session.commit()
          # on successful db insert, flash success
          flash('Artist '+form.name.data+' was just inserted!')  
  except:
          flash('An error occurred. Artist '+ form.name.data + ' could not be inserted!.')
          db.session.rollback()
  finally:
          db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

  form = VenueForm()
  venue = Venue.query.get(venue_id)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm()
  try:
          # find venue by id
          venue = Venue.query.get(venue_id)
          if venue is None: 
            flash('This venue was not exist')
            return render_template('forms/show_venue.html',form=form) 
          form.populate_obj(venue)
          db.session.add(venue) 
          db.session.commit()
          # on successful db insert, flash success
          flash('Venue '+form.name.data+' was just inserted!')  
  except:
          flash('An error occurred. Venue '+ form.name.data + ' could not be inserted!.')
          db.session.rollback()
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
  form = ArtistForm(request.form, meta={'csrf': False})

  if form.validate():
    try:
      new_artist = Artist()
      form.populate_obj(new_artist)
      db.session.add(new_artist) 
      db.session.commit()
      # on successful db insert, flash success
      flash('Artist '+form.name.data+' was just inserted!')  
    except:
          flash('An error occurred. Artist '+ form.name.data + ' could not be inserted!.')
          db.session.rollback()
    finally:
          db.session.close()
    return render_template('pages/home.html')
  else:
      errors = ", ".join([f"{field}: {error}" for field, errs in form.errors.items() for error in errs])
      flash(f'Please fix the following errors: {errors}')
      return render_template('forms/new_artist.html', form=form)  


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  data = []
                  
  shows = Show.query.all()
  for show in shows:
    data.append({
      "venue_id": show.venue_id,
      "venue_name": show.venue.name,
      "artist_id": show.artist_id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": format_datetime(str(show.start_time))
    })            
                  
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form, meta={'csrf': False})

  if form.validate():
      try:
          new_show = Show()
          form.populate_obj(new_show)
          db.session.add(new_show) 
          db.session.commit()
          # on successful db insert, flash success
          flash('A new show was just inserted!')  
      except:
          flash('An error occurred.')
          db.session.rollback()
      finally:
          db.session.close()
      return render_template('pages/home.html')
  else:
      errors = ", ".join([f"{field}: {error}" for field, errs in form.errors.items() for error in errs])
      flash(f'Please fix the following errors: {errors}')
      return render_template('forms/new_artist.html', form=form)     

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

# Specify port manually:

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
