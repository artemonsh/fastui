from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastui import FastUI, AnyComponent, prebuilt_html, components as c
from fastui.components.display import DisplayMode, DisplayLookup
from fastui.events import GoToEvent, BackEvent, PageEvent
from fastui.forms import fastui_form
from pydantic import BaseModel, Field

app = FastAPI()


class UserAdd(BaseModel):
    name: str = Field(title="Имя")
    dob: date = Field(title="Дата рождения")


class User(UserAdd):
    id: int


class UserDelete(BaseModel):
    id: int


users = [
    User(id=1, name='Артём', dob=date(1990, 1, 1)),
]


@app.post("/api/user")
def add_user(form: Annotated[UserAdd, fastui_form(UserAdd)]):
    print(f"{form=}")
    new_user = User(id=users[-1].id + 1 if users else 1, **form.model_dump())
    users.append(new_user)
    return [c.FireEvent(event=GoToEvent(url='/'))]


@app.post("/api/user/delete")
def add_user(form: Annotated[UserDelete, fastui_form(UserDelete)]):
    global users
    users = [user for user in users if user.id != form.id]
    return [c.FireEvent(event=GoToEvent(url='/'))]


@app.get("/api/user/add", response_model=FastUI, response_model_exclude_none=True)
def add_user_page():
    return [
        c.Page(
            components=[
                c.Link(components=[c.Text(text='Назад')], on_click=BackEvent()),
                c.Heading(text='Добавить пользователя', level=2),
                c.ModelForm(
                    model=UserAdd,
                    submit_url="/api/user"
                )
            ]
        )
    ]


@app.get("/api/", response_model=FastUI, response_model_exclude_none=True)
def users_table() -> list[AnyComponent]:
    return [
        c.Page(
            components=[
                c.Heading(text='Пользователи', level=2),
                c.Table(
                    data=users,
                    data_model=User,
                    columns=[
                        DisplayLookup(field='id'),
                        DisplayLookup(field='name', on_click=GoToEvent(url='/user/{id}/')),
                        DisplayLookup(field='dob', mode=DisplayMode.date),
                    ],
                ),
                c.Button(text="Добавить пользователя", on_click=GoToEvent(url="/user/add"))
            ]
        ),
    ]


@app.get("/api/user/{user_id}/", response_model=FastUI, response_model_exclude_none=True)
def user_profile(user_id: int) -> list[AnyComponent]:
    try:
        user = next(u for u in users if u.id == user_id)
    except StopIteration:
        raise HTTPException(status_code=404, detail="User not found")
    return [
        c.Page(
            components=[
                c.Heading(text=user.name, level=2),
                c.Link(components=[c.Text(text='Back')], on_click=BackEvent()),
                c.Details(data=user),
                c.Button(text="Удалить пользователя", on_click=PageEvent(name="delete-user")),
                c.Form(
                    submit_url="/api/user/delete",
                    form_fields=[
                        c.FormFieldInput(name='id', title='', initial=user_id, html_type='hidden')
                    ],
                    footer=[],
                    submit_trigger=PageEvent(name="delete-user"),
                ),
            ]
        ),
    ]


@app.get('/{path:path}')
async def html_landing() -> HTMLResponse:
    """Simple HTML page which serves the React app, comes last as it matches all paths."""
    return HTMLResponse(prebuilt_html(title='FastUI Demo'))
