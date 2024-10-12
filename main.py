from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from database import SessionLocal, engine, Base
from models import Contact as ContactModel
from schemas import ContactCreate, ContactUpdate, Contact as ContactSchema
from datetime import date, timedelta

app = FastAPI()

# Створення таблиць в базі даних
Base.metadata.create_all(bind=engine)

# Dependency для отримання сесії бази даних
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Створення нового контакту
@app.post("/contacts/", response_model=ContactSchema)
def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    db_contact = ContactModel(**contact.dict(exclude_unset=True))
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

# Отримання списку всіх контактів
@app.get("/contacts/", response_model=List[ContactSchema])
def get_contacts(db: Session = Depends(get_db)):
    return db.query(ContactModel).all()

# Отримання одного контакту за ідентифікатором
@app.get("/contacts/{contact_id}", response_model=ContactSchema)
def get_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

# Оновлення існуючого контакту
@app.put("/contacts/{contact_id}", response_model=ContactSchema)
def update_contact(contact_id: int, contact: ContactUpdate, db: Session = Depends(get_db)):
    db_contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    for key, value in contact.dict(exclude_unset=True).items():
        setattr(db_contact, key, value)
    
    db.commit()
    db.refresh(db_contact)
    return db_contact

# Видалення контакту
@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    db_contact = db.query(ContactModel).filter(ContactModel.id == contact_id).first()
    if db_contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    
    db.delete(db_contact)
    db.commit()
    return {"ok": True}

# Пошук контактів
@app.get("/contacts/search/", response_model=List[ContactSchema])
def search_contacts(
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(ContactModel)
    if first_name:
        query = query.filter(ContactModel.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(ContactModel.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(ContactModel.email.ilike(f"%{email}%"))
    
    return query.all()

# Отримання списку контактів з днями народження на найближчі 7 днів
@app.get("/contacts/birthdays/", response_model=List[ContactSchema])
def get_upcoming_birthdays(db: Session = Depends(get_db)):
    today = date.today()
    next_week = today + timedelta(days=7)
    return db.query(ContactModel).filter(ContactModel.birthday.between(today, next_week)).all()