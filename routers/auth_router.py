import datetime
import random
import jwt
from fastapi import APIRouter
from passlib.context import CryptContext
from starlette.responses import JSONResponse
from database import user_collection
from models import User, ResponseModel, AuthModel
from util.email import send_email, get_otp_template

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "pymongo_secret"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_otp():
    return random.randint(100000, 999999)


def generate_jwt(email: str):
    payload = {
        "email": email,
        "exp": datetime.datetime.now(datetime.UTC) + datetime.timedelta(hours=24),
        "iat": datetime.datetime.now(datetime.UTC)
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token


def decode_jwt_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload["email"]
    except jwt.ExpiredSignatureError:
        return "Token expired"
    except jwt.InvalidTokenError:
        return "Invalid token"


@router.post("/register")
async def register_user(user: User):
    user.email = user.email.lower()
    existing_user = await user_collection.find_one({
        "$or": [
            {"email": user.email},
            {"phone": user.phone}
        ]
    })
    if existing_user:
        payload = ResponseModel(status=False, status_code=400, message="Email or Phone number already exist")
        return JSONResponse(
            status_code=400,
            content=payload.model_dump()
        )

    user.password = hash_password(user.password)
    await user_collection.insert_one(user.model_dump(by_alias=True))
    payload = ResponseModel(status=False, status_code=201, message="User registered successfully")
    return JSONResponse(status_code=201, content=payload.model_dump())


@router.get("/get-otp")
async def get_otp(email: str):
    email = email.lower()
    existing_user = await user_collection.find_one({
        "$or": [
            {"email": email}
        ]
    })

    if not existing_user:
        payload = ResponseModel(status=False, status_code=400, message="User Not Exist, Please register user")
        return JSONResponse(status_code=400, content=payload.model_dump())
    elif existing_user.get("verified"):
        payload = ResponseModel(status=False, status_code=400, message="User already verified")
        return JSONResponse(status_code=400, content=payload.model_dump())
    else:
        otp = generate_otp()
        await user_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp": otp,
                }
            }
        )
    html_content = get_otp_template(otp)
    email_sent = send_email(
        subject="Password Reset OTP",
        recipient=email,
        html_content=html_content
    )
    print(f"OTP: ", otp)
    if email_sent:
        payload = ResponseModel(
            status=True,
            status_code=200,
            message="OTP has been sent to your email"
        )
    else:
        payload = ResponseModel(
            status=False,
            status_code=500,
            message="Failed to send OTP email. Please try again."
        )
    return JSONResponse(status_code=payload.status_code, content=payload.model_dump())

@router.post("/verify-otp")
async def verify_otp(email: str, otp: int):
    email = email.lower()
    existing_user = await user_collection.find_one({
        "$or": [{"email": email}]
    })

    if not existing_user:
        payload = ResponseModel(status=False, status_code=400, message="User Not Exist, Please register user")
        return JSONResponse(status_code=400, content=payload.model_dump())
    elif existing_user.get("verified"):
        payload = ResponseModel(status=False, status_code=400, message="User already verified")
        return JSONResponse(status_code=400, content=payload.model_dump())
    elif existing_user.get("otp") != otp:
        payload = ResponseModel(status=False, status_code=400, message="Invalid OTP, Please Try again")
        return JSONResponse(status_code=400, content=payload.model_dump())
    else:
        await user_collection.update_one({"email": email}, {"$set": {"verified": True}})
        payload = ResponseModel(status=True, status_code=200, message="OTP verification successful")
        return JSONResponse(status_code=200, content=payload.model_dump())


@router.post("/login")
async def login(user: User):
    user.email = user.email.lower()
    existing_user = await user_collection.find_one({
        "$or": [{
            "email": user.email
        }]
    })

    if not existing_user:
        payload = ResponseModel(status=False, status_code=400, message="User Not Exist, Please register user")
        return JSONResponse(status_code=400, content=payload.model_dump())
    elif not existing_user.get("verified"):
        payload = ResponseModel(status=False, status_code=400, message="Verify User Account")
        return JSONResponse(status_code=400, content=payload.model_dump())
    elif not verify_password(user.password, existing_user.get('password')):
        payload = ResponseModel(status=False, status_code=400, message="Incorrect password")
        return JSONResponse(status_code=400, content=payload.model_dump())
    else:
        token = generate_jwt(user.email)
        await user_collection.update_one({"email": user.email}, {"$set": {"token": token}})
        data = AuthModel(token=token, email=user.email)
        payload = ResponseModel(status=True, status_code=200, message="User Login Successful", data=data.model_dump())
        return JSONResponse(status_code=200, content=payload.model_dump())


@router.post("/forgot-password")
async def forgot_password(email: str):
    email = email.lower()
    existing_user = await user_collection.find_one({
        "$or": [{"email": email}]
    })

    if not existing_user:
        payload = ResponseModel(status=False, status_code=400, message="User Not Exist, Please register user")
        return JSONResponse(status_code=400, content=payload.model_dump())

        otp = generate_otp()
        await user_collection.update_one(
            {"email": email},
            {
                "$set": {
                    "otp": otp,
                }
            }
        )

    html_content = get_otp_template(otp)
    email_sent = send_email(
        subject="Password Reset OTP",
        recipient=email,
        html_content=html_content
    )

    if email_sent:
        payload = ResponseModel(
            status=True,
            status_code=200,
            message="OTP has been sent to your email"
        )
    else:
        payload = ResponseModel(
            status=False,
            status_code=500,
            message="Failed to send OTP email. Please try again."
        )
    return JSONResponse(status_code=payload.status_code, content=payload.model_dump())


@router.post("/reset-password")
async def reset_password(user: User):
    user.email = user.email.lower()
    existing_user = await user_collection.find_one({
        "$or": [{
            "email": user.email
        }]
    })

    if not existing_user:
        payload = ResponseModel(status=False, status_code=400, message="User Not Exist, Please register user")
        return JSONResponse(status_code=400, content=payload.model_dump())
    else:
        password = hash_password(user.password)
        await user_collection.update_one({"email": user.email}, {"$set": {"password": password}})
        payload = ResponseModel(status=True, status_code=200, message="User Login Successful")
        return JSONResponse(status_code=200, content=payload.model_dump())
