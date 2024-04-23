from typing import Literal, Optional

from cachetools import Cache, cached
from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..entities.models import OrganizationRef, ServiceRef
from ..schemas import Creator
from ..schemas.attribute import Attribute
from ..utils.teia_behaviors import Authoring


class AuthProviderDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    created_by: Creator
    external_ids: list[Attribute] = Field(
        default_factory=list
    )  # dynamic provider selection: issuer, audience
    extra: list[Attribute]  # url, client_id, client_secret
    organization_ref: OrganizationRef
    service_ref: Optional[ServiceRef]
    type: Literal["auth0", "melt-key", "tauth-key"]

    @classmethod
    def collection_name(cls) -> str:
        return "authproviders"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel([("external_ids.name", 1), ("external_ids.value", 1)]),
        ]
        return idxs

    def get_external_id(self, name: str) -> Optional[str]:
        if not hasattr(self, "_ext_ids"):
            self._ext_ids = {item.name: item.value for item in self.external_ids}
        return self._ext_ids.get(name)
