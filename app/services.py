from .tables import User, Project

def create_user(session, name, email, bio="", skills=""):
    user = User(name=name, email=email, bio=bio, skills=skills)
    session.add(user)
    session.commit()
    return user

def create_project(session, title, description, leader_id):
    project = Project(title=title, description=description, leader_id=leader_id)
    session.add(project)
    session.commit()
    return project

def get_all_projects(session):
    return session.query(Project).all()