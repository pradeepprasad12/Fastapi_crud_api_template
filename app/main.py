from fastapi import FastAPI, Depends, HTTPException,Request
from sqlalchemy.orm import Session
from . import models, schemas, crud
from .database import SessionLocal, engine
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from . import utils
from fastapi import Security

# Initialize the database
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")  

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# @app.post("/items/", response_model=schemas.ItemResponse)
# def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db)):
#     return crud.create_item(db=db, item=item)

@app.get("/items/", response_model=list[schemas.ItemResponse])
def read_items(db: Session = Depends(get_db)):
    return crud.get_items(db)

@app.get("/items/{item_id}", response_model=schemas.ItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    item = crud.get_item(db=db, item_id=item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.put("/items/{item_id}", response_model=schemas.ItemResponse)
def update_item(item_id: int, item: schemas.ItemUpdate, db: Session = Depends(get_db)):
    updated_item = crud.update_item(db, item_id, item)
    if updated_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated_item



#tempalting
@app.get("/")
def read_home(request: Request, db: Session = Depends(get_db)):
    items = crud.get_items(db)  
    return templates.TemplateResponse("index.html", {"request": request, "items": items})

@app.delete("/items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    success = crud.delete_item(db, item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@app.post("/signup/", response_model=schemas.UserResponse)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    return crud.create_user(db, user)

# @app.post("/login/")
# def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
#     authenticated_user = crud.authenticate_user(db, user.email, user.password)
#     if not authenticated_user:
#         raise HTTPException(status_code=401, detail="Invalid email or password")

#     return {"message": "Login successful", "user_id": authenticated_user.id, "email": authenticated_user.email}


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@app.post("/login/")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user_data = crud.login_user(db, form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    return user_data


def get_current_user(token: str = Security(oauth2_scheme)):
    payload = utils.verify_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload["sub"]  # Return the email of the logged-in user

@app.post("/items/", response_model=schemas.ItemResponse)
def create_item(item: schemas.ItemCreate, db: Session = Depends(get_db), user_email: str = Depends(get_current_user)):
    return crud.create_item(db=db, item=item)