from fastapi import FastAPI, Response
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

#классы группа и участник

class Group(BaseModel):
    id: int
    name: str
    description: Optional[str] = None # не обязательный параметр
    participants: Optional[List] = None
    
    def update(self, group_data: dict) -> dict:
        name = group_data.get('name')
        description = group_data.get('description')
        participants = group_data.get('participants')
        
        if name is not None:
            self.name = name
        if description is not None:
            self.description = description
        else:
            self.description = ""
        
        if participants is not None:
            self.participants.append(participants)

        return self.dict()
    


class Participant(BaseModel):
    id: int
    name: str
    wish: Optional[str] = None # не обязательный параметр

class PartWithRec(Participant):
    recipient: Optional[Participant] = None

#группа с участником
class GroupWithParts(Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_part(self, part: Participant) -> dict:
        if part is not None:
            group_data = {"participants": part.dict()}
        else:
            group_data=None
        return super().update(group_data)
        
        # raise ValueError("group or part not found")

#сервисы для методов группы

class GroupService:
    GROUPS = list()
    
    def create_group(self, group: dict) -> int:
        name = group.get('name')
        description = group.get('description')
        if not name:
            raise ValueError("Name is required")
        new_id = len(self.GROUPS) + 1
        entity = Group(
            id=new_id,
            name=name,
            description=description,
            participants=list(),
        )
        self.GROUPS.append(entity)
        return new_id

    def get_all_groups(self) -> List[GroupWithParts]:
        result = list()
        for group in self.GROUPS:
            new = GroupWithParts(
                id=group.id,
                name=group.name,
                description=group.description,
                participants=group.participants
            )
            result.append(new)
        return result

    def get_group_by_id(self, group_id: int) -> GroupWithParts:
        for group in self.GROUPS:
            if group.id == group_id:
                return group
        raise ValueError("group not found")
 
    def update_group(self, group_id: int, group: GroupWithParts) -> bool:
        for i, p in enumerate(self.GROUPS):
            if p.id == group_id:
                print(self.GROUPS)
                self.GROUPS[i] = group
                
                print(self.GROUPS)
                return True
        raise ValueError("group not found")

    def delete_group(self, group_id: int) -> bool:
        for i, group in enumerate(self.GROUPS):
            if group.id == group_id:
                del self.GROUPS[i]
                return True
        raise ValueError("group not found")   


class UpdatedGroupAction(Group):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def update(self, group_data: dict) -> dict:
        return super().update(group_data)
    
#сервисы для методов участника

class PartService:
    PARTICIPANTS = list()
    
    def create_part(self, part: dict) -> int:
        name = part.get('name')
        wish = part.get('wish')
        if not name:
            raise ValueError("Name is required")
        new_id = len(self.PARTICIPANTS) + 1
        entity = Participant(
            id=new_id,
            name=name,
            wish=wish,
        )
        self.PARTICIPANTS.append(entity)
        return new_id
    
    def get_all_parts(self) -> List[Participant]:
        result = list()
        for part in self.PARTICIPANTS:
            new = Participant(
                id=part.id,
                name=part.name,
                description=part.description
            )
            result.append(new)
        return result

    def get_part_by_id(self, part_id: int) -> Participant:
        for part in self.PARTICIPANTS:
            if part.id == part_id:
                return part
        raise ValueError("part not found")


#роуты группы

group_service=GroupService()
@app.post("/group", responses={201: {"description": "Group created successfully"}, 400: {"description": "Invalid input"}})
async def create_group(group: dict, response: Response):
    try:
        new_id = group_service.create_group(group)
        response.status_code = 201
        return {"group_id": new_id}
    except ValueError as e:
        response.status_code = 400
        return {"error": str(e)}

@app.get("/groups", responses={200: {"description": "Successful Response"}})
def get_all_groups(response: Response):
    groups = group_service.get_all_groups()
    return groups

@app.get("/group/{group_id}", responses={200: {"description": "Successful Response"}, 404: {"description": "Not Found"}})
def get_group(group_id: int, response: Response):
    try:
        group = group_service.get_group_by_id(group_id)
        return group.__dict__
    except ValueError as e:
        response.status_code = 404
        return {"error": str(e)}


@app.put('/group/{group_id}', responses={200: {"description": "Successful Response"}, 404: {"description": "Not Found"}})
def edit_group(group_id: int, group: dict, response: Response):
    try:
        group_entity = group_service.get_group_by_id(group_id)
        updated_entity = UpdatedGroupAction(**group_entity.dict())
        updated_entity.update(group)
        group_service.update_group(group_id, updated_entity)
        return {"message": "group updated successfully"}
    except ValueError as e:
        response.status_code = 404
        return {"error": str(e)}

#Редактировать можно только свойства name, description
#Удалить название таким образом нельзя, описание – можно


@app.delete("/group/{group_id}", responses={204: {"description": "Successful Response"}, 404: {"description": "Not Found"}})
async def delete_group(group_id: int, response: Response):
    try: 
        group_service.delete_group(group_id)
        response.status_code = 204
        return {"message": "group has been deleted successfully"}
    except ValueError as e:
        response.status_code = 404
        return {"error": str(e)}


#роуты участника

part_service=PartService()
@app.post("/group/{group_id}/participant", responses={201: {"description": "Part created successfully"}, 400: {"description": "Invalid input"}})
async def create_group(part: dict, group_id: int, response: Response):
    try:
        # добавление участника к группе
        group_entity = group_service.get_group_by_id(group_id)
        new_id = part_service.create_part(part)
        group_with_part = GroupWithParts(**group_entity.dict())
        group_with_part.add_part(part_service.get_part_by_id(new_id))
        group_service.update_group(group_id, group_with_part)

        
        response.status_code = 201
        return {"part_id": new_id}
    
    except ValueError as e:
        response.status_code = 400
        return {"error": str(e)}

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080)