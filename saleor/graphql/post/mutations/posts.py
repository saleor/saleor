from collections import defaultdict
from datetime import date

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction

from ....attribute import AttributeType
from ....post import models
from ...attribute.utils import AttributeAssignmentMixin
from ...core.mutations import BaseMutation, ModelDeleteMutation, ModelMutation
from ...core.types.common import PostError
from ...core.utils import clean_seo_fields, validate_slug_and_generate_if_needed
from ...core.types import SeoInput, Upload
from ...utils.validators import check_for_duplicates
from ....core.permissions import PostPermissions
from ....core.exceptions import PermissionDenied
from ....post.utils import delete_posts
from ..types import Post, PostMedia
from ...store.types import Store
from ....post.error_codes import PostErrorCode
from ....product import ProductMediaTypes
from ...channel import ChannelContext
from ....product.thumbnails import (
    create_store_background_image_thumbnails,
)
from ...core.utils import (
    clean_seo_fields,
    from_global_id_strict_type,
    get_duplicated_values,
    validate_image_file,
)

class PostInput(graphene.InputObjectType):
    title = graphene.String(description="Post title.")
    content = graphene.JSONString(description="post full content (JSON).")

class PostCreateInput(PostInput):
    store = graphene.ID(
        description="ID of the store that post belongs to.", required=True
    )

class PostCreate(ModelMutation):
    class Arguments:
        input = PostCreateInput(
            required=True, description="Fields required to create a post."
        )

    class Meta:
        description = "Creates a new post."
        model = models.Post
        permissions = (PostPermissions.MANAGE_POSTS,)
        error_type_class = PostError
        error_type_field = "post_errors"
    
    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        store_id = data["store_id"]
        if store_id:
            store = cls.get_node_or_error(
                info, store_id, field="store", only_type=Store
            )
            cleaned_input["store"] = store

        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info, **data):
        store_id = data.pop("store_id", None)
        data["input"]["store_id"] = store_id
        return super().perform_mutation(root, info, **data)

    @classmethod
    def save(cls, info, instance, cleaned_input):
        instance.save()


class PostUpdate(PostCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a post to update.")
        input = PostInput(
            required=True, description="Fields required to update a post."
        )

    class Meta:
        description = "Updates a post."
        model = models.Post
        permissions = (PostPermissions.MANAGE_POSTS,)
        error_type_class = PostError
        error_type_field = "post_errors"


class PostDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a post to delete.")

    class Meta:
        description = "Deletes a post."
        model = models.Post
        permissions = (PostPermissions.MANAGE_POSTS,)
        error_type_class = PostError
        error_type_field = "Post_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        if not cls.check_permissions(info.context):
            raise PermissionDenied()
        node_id = data.get("id")
        instance = cls.get_node_or_error(info, node_id, only_type=Post)

        db_id = instance.id
        delete_posts([db_id])
        instance.id = db_id
        return cls.success_response(instance)

class PostMediaCreateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a post media.")
    image = Upload(
        required=False, description="Represents an image file in a multipart request."
    )
    post = graphene.ID(
        required=True, description="ID of an product.", name="post"
    )


class PostMediaCreate(ModelMutation):
    post = graphene.Field(Post)
    media = graphene.Field(PostMedia)

    class Arguments:
        input = PostMediaCreateInput(
            required=True, description="Fields required to create a product media."
        )

    class Meta:
        description = (
            "Create a media object (image or video URL) associated with product. "
            "For image, this mutation must be sent as a `multipart` request. "
            "More detailed specs of the upload format can be found here: "
            "https://github.com/jaydenseric/graphql-multipart-request-spec"
        )
        permissions = (PostPermissions.MANAGE_POSTS,)
        model = models.PostMedia
        error_type_class = PostError
        error_type_field = "post_errors"

    @classmethod
    def validate_input(cls, data):
        image = data.get("image")
        
        if not image:
            raise ValidationError(
                {
                    "input": ValidationError(
                        "Image is required.",
                        code=PostErrorCode.REQUIRED,
                    )
                }
            )

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        data = data.get("input")
        cls.validate_input(data)
        post = cls.get_node_or_error(
            info, data["post"], field="post", only_type=Post
        )

        alt = data.get("alt", "")
        image = data.get("image")

        if image:
            image_data = info.context.FILES.get(image)
            validate_image_file(image_data, "image")
            media = post.media.create(
                image=image_data, alt=alt, type=ProductMediaTypes.IMAGE
            )            

        post = ChannelContext(node=post, channel_slug=None)
        return super().success_response(post)


class PostMediaUpdateInput(graphene.InputObjectType):
    alt = graphene.String(description="Alt text for a product media.")


class PostMediaUpdate(BaseMutation):
    post = graphene.Field(Post)
    media = graphene.Field(PostMedia)

    class Arguments:
        id = graphene.ID(required=True, description="ID of a post media to update.")
        input = PostMediaUpdateInput(
            required=True, description="Fields required to update a post media."
        )

    class Meta:
        description = "Updates a post media."
        permissions = (PostPermissions.MANAGE_POSTS,)
        error_type_class = PostError
        error_type_field = "post_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        media = cls.get_node_or_error(info, data.get("id"), only_type=PostMedia)
        post = media.post
        alt = data.get("input").get("alt")
        if alt is not None:
            media.alt = alt
            media.save(update_fields=["alt"])
        post = ChannelContext(node=post, channel_slug=None)
        return PostMediaUpdate(product=post, media=media)


class PostMediaReorder(BaseMutation):
    post = graphene.Field(Post)
    media = graphene.List(graphene.NonNull(PostMedia))

    class Arguments:
        post_id = graphene.ID(
            required=True,
            description="ID of post that media order will be altered.",
        )
        media_ids = graphene.List(
            graphene.ID,
            required=True,
            description="IDs of a product media in the desired order.",
        )

    class Meta:
        description = "Changes ordering of the product media."
        permissions = (PostPermissions.MANAGE_POSTS,)
        error_type_class = PostError
        error_type_field = "post_errors"

    @classmethod
    def perform_mutation(cls, _root, info, post_id, media_ids):
        post = cls.get_node_or_error(
            info, post_id, field="post_id", only_type=Post
        )
        if len(media_ids) != post.media.count():
            raise ValidationError(
                {
                    "order": ValidationError(
                        "Incorrect number of media IDs provided.",
                        code=PostErrorCode.INVALID,
                    )
                }
            )

        ordered_media = []
        for media_id in media_ids:
            media = cls.get_node_or_error(
                info, media_id, field="order", only_type=PostMedia
            )
            if media and media.post != post:
                raise ValidationError(
                    {
                        "order": ValidationError(
                            "Media %(media_id)s does not belong to this product.",
                            code=PostErrorCode.INVALID,
                            params={"media_id": media_id},
                        )
                    }
                )
            ordered_media.append(media)

        for order, media in enumerate(ordered_media):
            media.sort_order = order
            media.save(update_fields=["sort_order"])

        post = ChannelContext(node=post, channel_slug=None)
        return PostMediaReorder(post=post, media=ordered_media)
