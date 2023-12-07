from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, Session, relationship, joinedload
from sqlalchemy.ext.declarative import DeclarativeMeta, declared_attr
from sqlalchemy.orm import sessionmaker
import uuid
from typing import List

DATABASE_URL = "mysql+mysqlconnector://admin:12345678@database-1.crvlwakzi7le.us-east-1.rds.amazonaws.com:3306/iresident_db"
Base: DeclarativeMeta = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()


# origins = [
#     "http://localhost",
#     "http://localhost:3000",  # Si estás usando React en el puerto 3000
# ]
#
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    usuarios = relationship("User", back_populates="rol")


class User(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    direccion = Column(String)
    telefono = Column(String)
    email = Column(String)
    fecha_ingreso = Column(Date)
    rol_id = Column(Integer, ForeignKey("roles.id"))
    rol = relationship("Role", back_populates="usuarios")
    visitantes = relationship("Visitor", back_populates="usuarios")
    vehiculos = relationship("Vehicle", back_populates="usuario")
    invitaciones = relationship("Invitation", back_populates="usuario")


class Visitor(Base):
    __tablename__ = "visitantes"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String, index=True)
    fecha_visita = Column(Date)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuarios = relationship("User", back_populates="visitantes")
    invitaciones = relationship("Invitation", back_populates="visitante")


class Vehicle(Base):
    __tablename__ = "vehiculos"
    id = Column(Integer, primary_key=True, index=True)
    placa = Column(String, index=True)
    marca = Column(String)
    modelo = Column(String)
    color = Column(String)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    usuario = relationship("User", back_populates="vehiculos")


class Invitation(Base):
    __tablename__ = "invitaciones"
    id = Column(String, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))
    visitante_id = Column(Integer, ForeignKey("visitantes.id"))
    fecha_invitacion = Column(DateTime)
    canjeada = Column(Boolean, default=False)
    usuario = relationship("User", back_populates="invitaciones")
    visitante = relationship("Visitor", back_populates="invitaciones")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


#
#
#             ROLES
#
#
@app.get("/roles/", response_model=None)
def read_roles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    roles = db.query(Role).offset(skip).limit(limit).all()
    return roles


@app.get("/roles/{role_id}")
def get_role(role_id: int, db: Session = Depends(get_db)):
    role = db.query(Role).filter(Role.id == role_id).first()
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role


# @app.get("/users/")
# def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     users = db.query(User).offset(skip).limit(limit).all()
#     return users
#
# @app.get("/users/{user_id}")
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.id == user_id).first()
#     if user is None:
#         raise HTTPException(status_code=404, detail="User nor found")
#     return user


#
#
#        USUARIOS
#
#
@app.post("/usuarios/", response_model=None)
def create_user(user: dict, db: Session = Depends(get_db)):
    db.add(User(**user))
    db.commit()
    db.refresh(user)
    return user


@app.get("/usuarios/", response_model=None)
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = (db.query(User)
             .offset(skip)
             .limit(limit)
             .all())

    return users


@app.get("/usuarios/{user_id}", response_model=None)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = (db.query(User)
            .filter(User.id == user_id)
            .options(joinedload(User.vehiculos))
            .first())
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.put("/usuarios/{user_id}", response_model=None)
def update_user(user_id: int, updated_user: dict, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for key, value in updated_user.dict().items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user


@app.delete("/usuarios/{user_id}", response_model=None)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db.delete(user)
    db.commit()
    return user


@app.post("/login/", response_model=None)
def login(user_data: dict, db: Session = Depends(get_db)):
    user = (db.query(User)
            .filter(User.email == user_data["email"])
            .options(joinedload(User.vehiculos))
            .first())
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


#
#
#        VISITANTES
#
#
@app.post("/visitantes/", response_model=None)
def create_visitor(visitor: dict, db: Session = Depends(get_db)):
    visitor = Visitor(**visitor)
    db.add(visitor)
    db.commit()
    db.refresh(visitor)
    return visitor


@app.get("/visitantes/", response_model=None)
def read_visitors(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    visitors = db.query(Visitor).offset(skip).limit(limit).all()
    return visitors


@app.get("/visitantes/{visitor_id}", response_model=None)
def read_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    return visitor


@app.put("/visitantes/{visitor_id}", response_model=None)
def update_visitor(visitor_id: int, updated_visitor: dict, db: Session = Depends(get_db)):
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    for key, value in updated_visitor.dict().items():
        setattr(visitor, key, value)
    db.commit()
    db.refresh(visitor)
    return visitor


@app.delete("/visitantes/{visitor_id}", response_model=None)
def delete_visitor(visitor_id: int, db: Session = Depends(get_db)):
    visitor = db.query(Visitor).filter(Visitor.id == visitor_id).first()
    if visitor is None:
        raise HTTPException(status_code=404, detail="Visitor not found")
    db.delete(visitor)
    db.commit()
    return visitor


#
#
#        VEHICULOS
#
#
@app.post("/vehiculos/", response_model=None)
def create_vehicle(vehicle: dict, db: Session = Depends(get_db)):
    db.add(Vehicle(**vehicle))
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.get("/vehiculos/", response_model=None)
def read_vehicles(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).offset(skip).limit(limit).all()
    return vehicles


@app.get("/vehiculos/{vehicle_id}", response_model=None)
def read_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return vehicle


@app.put("/vehiculos/{vehicle_id}", response_model=None)
def update_vehicle(vehicle_id: int, updated_vehicle: dict, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    for key, value in updated_vehicle.dict().items():
        setattr(vehicle, key, value)
    db.commit()
    db.refresh(vehicle)
    return vehicle


@app.delete("/vehiculos/{vehicle_id}", response_model=None)
def delete_vehicle(vehicle_id: int, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if vehicle is None:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.commit()
    return vehicle


#
#
#       INVITACIONES
#
#
@app.post("/invitacion/")
def make_invitation(invitation_data: dict, db: Session = Depends(get_db)):
    uuid_value = str(uuid.uuid4())

    invitation_data['id'] = uuid_value

    db.add(Invitation(**invitation_data))
    db.commit()
    # db.refresh(Invitation(**invitation_data))

    return {"code": uuid_value}


@app.post("/invitacion/redeem/")
def redeem_invitation(inv_data: dict, db: Session = Depends(get_db)):
    invitation = db.query(Invitation).filter(Invitation.id == inv_data["code"]).first()
    if invitation is None:
        raise HTTPException(status_code=404, detail="Invitation not found")

    if invitation.canjeada:
        raise HTTPException(status_code=400, detail="Invitation already redeemed")

    invitation.canjeada = True

    db.commit()
    db.refresh(invitation)
    return invitation


@app.get("/invitation/{code}")
def read_invitation(code: str, db: Session = Depends(get_db)):
    inv = db.query(Invitation).options(joinedload(Invitation.usuario)).filter(Invitation.id == code).first()
    return inv

# if __name__ == "__main__":
#     import uvicorn
#
#     uvicorn.run(app, host="127.0.0.1", port=8000)
