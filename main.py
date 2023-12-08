import streamlit as st
from streamlit import session_state
from streamlit_drawable_canvas import st_canvas
from streamlit_server_state import (
    server_state,
    server_state_lock,
    force_rerun_bound_sessions
)
from time import time

class Room:
    def __init__(self, name):
        self.name = name
        self.players = set()
        self.image = None
    
    def __str__(self):
        return self.name

    def participate(self, nickname):
        self.players.add(nickname)
    
    def is_participated(self, nickname):
        return nickname in self.players


def nickname_submitted():
    session_state.nickname_created = True
    session_state.nickname = session_state.new_nickname

def room_enter_clicked():
    session_state.room_entered = True
    with server_state_lock.rooms:
        server_state.rooms[session_state.radio_choose].participate(session_state.nickname)
        session_state.room_name = session_state.radio_choose

def room_created():
    session_state.room_entered = True
    with server_state_lock.rooms:
        room = Room(session_state.new_room_name)
        room.participate(session_state.nickname)
        server_state.rooms[session_state.new_room_name] = room
        session_state.room_name = session_state.new_room_name

if "rooms" not in server_state:
    with server_state_lock.rooms:
        server_state.rooms = {}

initial_items = [
    ("last_draw", 0),
    ("nickname", ""),
    ("nickname_created", False),
    ("room_entered", False),
    ("mode", "Default"),
    ("room_name", "Undefined")
]

for key, value in initial_items:
    if key not in session_state:
        session_state[key] = value

if session_state.room_entered:
    st.text("Nickname : " + session_state.nickname)
    st.text("Room : " + str(session_state.room_name))
    stroke_width = st.sidebar.slider("Stroke width: ", 1, 25, 3)
    stroke_color = st.sidebar.color_picker("Stroke color hex: ")
    session_state.mode = st.selectbox("Mode : ", ["Drawer", "Guesser"])
elif not session_state.nickname_created:
    st.text_input("Nickname", key="new_nickname", on_change=nickname_submitted)
else:
    st.text("Nickname : " + session_state.nickname)
    with server_state_lock.rooms:
        st.markdown("### Create new Room or Choose Room to Enter")
        st.text_input("Room Name", key="new_room_name", on_change=room_created)
        st.radio("Room to enter", [room.name for room in server_state.rooms.values()], key="radio_choose")
        st.button("Enter", on_click=room_enter_clicked)

if session_state.mode == "Drawer":
    canvas_result = st_canvas(
        fill_color="rgba(255, 165, 0, 0.3)",
        stroke_width=stroke_width,
        stroke_color=stroke_color,
        background_color="#fff",
        background_image=None,
        update_streamlit=True,
        height=450,
        drawing_mode="freedraw",
        point_display_radius=0,
        key="canvas",
    )

    if canvas_result.json_data is None:
        cur_draw = 0
    else:
        cur_draw = len(canvas_result.json_data["objects"])
    
    if st.session_state.last_draw != cur_draw:
        st.session_state.last_draw = cur_draw

        with server_state_lock.rooms:
            server_state.rooms[session_state.room_name].image = canvas_result.image_data
            force_rerun_bound_sessions("rooms")

if session_state.mode == "Guesser":
    with server_state_lock.rooms:
        if server_state.rooms[session_state.room_name].image is not None:
            st.image(server_state.rooms[session_state.room_name].image)
