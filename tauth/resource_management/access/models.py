from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document
from redbaby.pyobjectid import PyObjectId

from ...entities.schemas import EntityRef
from ...utils.teia_behaviors import Authoring


class ResourceAcessDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    """
    Resource Acess controls the injection of the resource into the OPA context
    Having a ResourceAcess does not mean anything other than that.
    If you have READ, WRITE or ADMIN is up to the REGO Policy
    """

    resource_id: PyObjectId
    entity_ref: EntityRef
