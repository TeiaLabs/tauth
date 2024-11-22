from typing import Literal

from pydantic import Field
from pymongo import IndexModel
from redbaby.behaviors.objectids import ObjectIdMixin
from redbaby.behaviors.reading import ReadingMixin
from redbaby.document import Document

from ..entities.schemas import OrganizationRef, ServiceRef
from ..schemas.attribute import Attribute
from ..utils.teia_behaviors import Authoring


class AuthProviderDAO(Document, Authoring, ObjectIdMixin, ReadingMixin):
    external_ids: list[Attribute] = Field(
        default_factory=list
    )  # dynamic provider selection: issuer, audience
    extra: list[Attribute] = Field(
        default_factory=list
    )  # url, client_id, client_secret, user_info_url
    organization_ref: OrganizationRef
    service_ref: ServiceRef
    type: Literal["auth0", "melt-key", "okta", "tauth-key"]

    @classmethod
    def collection_name(cls) -> str:
        return "authproviders"

    @classmethod
    def indexes(cls) -> list[IndexModel]:
        idxs = [
            IndexModel(
                [
                    ("type", 1),
                    ("organization_ref.handle", 1),
                    ("service_ref.handle", 1),
                ],
                unique=True,
            ),
            IndexModel([("external_ids.name", 1), ("external_ids.value", 1)]),
        ]
        return idxs

    def get_external_id(self, name: str) -> str | None:
        if not hasattr(self, "_ext_ids"):
            self._ext_ids = {item.name: item.value for item in self.external_ids}
        return self._ext_ids.get(name)
