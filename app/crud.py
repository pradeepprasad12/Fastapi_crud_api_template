from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, crud,utils
from app.database import SessionLocal, engine
from .models import Item
from datetime import timedelta

def get_items(db: Session):
    return db.query(models.Item).all()

def get_item(db: Session, item_id: int):
    return db.query(models.Item).filter(models.Item.id == item_id).first()


def delete_item(db: Session, item_id: int):
    item = db.query(Item).filter(Item.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        return True
    return False

def create_item(db: Session, item: schemas.ItemCreate):
    db_item = models.Item(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def delete_item(db: Session, item_id: int):
    item = get_item(db, item_id)
    if item:
        db.delete(item)
        db.commit()

def delete_item(db: Session, item_id: int):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
        return {"message": "Item deleted successfully"}
    return None


def update_item(db: Session, item_id: int, item_data: schemas.ItemUpdate):
    item = db.query(models.Item).filter(models.Item.id == item_id).first()
    if not item:
        return None  

    for key, value in item_data.dict(exclude_unset=True).items():
        setattr(item, key, value) 

    db.commit()
    db.refresh(item)  
    return item

# user createing

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = utils.hash_password(user.password)  # Hash the password
    new_user = models.User(name=user.name, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user and utils.verify_password(password, user.hashed_password):
        return user
    return None 


def login_user(db, email: str, password: str):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not utils.verify_password(password, user.hashed_password):
        return None  # Authentication failed
    
    # Generate a JWT token for the user
    access_token = utils.create_access_token(data={"sub": user.email}, expires_delta=timedelta(hours=1))
    return {"access_token": access_token, "token_type": "bearer"}