import logging

from django.apps import apps
from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.db.models import Q
from django.db.models.base import ModelBase
from django.db.models.constraints import CheckConstraint, UniqueConstraint
from django.db.models.functions import Lower
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from . import LOVValueType
from .exceptions import ModelClassParsingError, IncorrectSubclassError


class LOVEntityModelBase(ModelBase):
    """
    Models extending EntityModelBase get a ForeignKey to the model class specified in lov_entity_model
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        model = super().__new__(cls, name, bases, attrs, **kwargs)

        for base in bases:
            if base.__name__ == "AbstractLOVSelection" or base.__name__ == "AbstractLOVValue":
                ConcreteLOVModel = model

                if not ConcreteLOVModel._meta.abstract and ConcreteLOVModel.lov_entity_model is not None:
                    if isinstance(ConcreteLOVModel.lov_entity_model, str):
                        # Parse string representation of the target entity model class
                        try:
                            app_label, model_name = ConcreteLOVModel.lov_entity_model.split(".")
                        except ValueError as e:
                            raise ModelClassParsingError(e)
                        ConcreteLOVModel.lov_entity_model = apps.get_model(app_label, model_name, require_ready=False)

                    ConcreteLOVModel.add_to_class(
                        "lov_entity",
                        models.ForeignKey(
                            ConcreteLOVModel.lov_entity_model,
                            on_delete=ConcreteLOVModel.lov_entity_on_delete,
                            related_name=ConcreteLOVModel.lov_entity_model_related_name,
                            related_query_name=ConcreteLOVModel.lov_entity_model_related_query_name,
                            blank=True,
                            null=True,
                        ),
                    )
                else:
                    raise IncorrectSubclassError("lov_value_model must be specified for concrete subclasses of AbstractLOVSelection")

        return model


class LOVValueModelBase(EntityModelBase):
    """
    Models extending EntityAndValueModelBase get a ForeignKey to the model class specified in lov_entity_model
        and a ManyToManyField to the model specified in lov_value_model

    Used to set up the ManyToManyField from concrete classes of AbstractLOVSelection
        to concrete classes of AbstractLOVValue.

    Within the model, set the `lov_value_model` parameter to the concrete class inheriting AbstractLOVValue
        and `lov_entity_model` to the model entity which is associated with both LOV concrete classes.

        For instance:

            class ConcreteLOVValue(AbstractLOVValue):
                lov_entity_model = SomeModel
                # or `lov_entity_model = "myapp.SomeModel"`

            class ConcreteLOVSelection(AbstractLOVSelection):
                lov_value_model = ConcreteLOVValue
                # or `lov_value_model = "myapp.ConcreteLOVValue"`

                lov_entity_model = SomeModel
                # or `lov_entity_model = "myapp.SomeModel"`
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        model = super().__new__(cls, name, bases, attrs, **kwargs)

        for base in bases:
            if base.__name__ == "AbstractLOVValue":
                ConcreteLOVValueModel = model

                if (
                    not ConcreteLOVValueModel._meta.abstract
                    and ConcreteLOVValueModel.lov_selections_model is not None
                    and ConcreteLOVValueModel.lov_entity_model is not None
                ):
                    if isinstance(ConcreteLOVValueModel.lov_selections_model, str):
                        # Parse string representation of the target selection model class
                        try:
                            app_label, model_name = ConcreteLOVValueModel.lov_selections_model.split(".")
                        except ValueError as e:
                            raise ModelClassParsingError(e)
                        ConcreteLOVValueModel.lov_selections_model = apps.get_model(
                            app_label, model_name, require_ready=False
                        )

                    if isinstance(ConcreteLOVValueModel.lov_entity_model, str):
                        # Parse string representation of the target entity model class
                        try:
                            app_label, model_name = ConcreteLOVValueModel.lov_entity_model.split(".")
                        except ValueError as e:
                            raise ModelClassParsingError(e)
                        ConcreteLOVValueModel.lov_entity_model = apps.get_model(
                            app_label, model_name, require_ready=False
                        )

                    ConcreteLOVValueModel.add_to_class(
                        "lov_associated_entities",
                        models.ManyToManyField(
                            ConcreteLOVValueModel.lov_entity_model,
                            through=ConcreteLOVValueModel.lov_selections_model,
                            through_fields=("lov_value", "lov_entity"),
                            related_name=ConcreteLOVValueModel.lov_associated_entities_related_name,  # "selected"
                            related_query_name=ConcreteLOVValueModel.lov_associated_entities_related_query_name,
                        ),
                    )
                else:
                    raise IncorrectSubclassError("lov_value_model must be specified for concrete subclasses of AbstractLOVValue")

        return model



class LOVSelectionModelBase(EntityModelBase):
    """
    Models extending EntityAndValueModelBase get a ForeignKey to the model class specified in lov_entity_model
        and a ManyToManyField to the model specified in lov_value_model

    Used to set up the ManyToManyField from concrete classes of AbstractLOVSelection
        to concrete classes of AbstractLOVValue.

    Within the model, set the `lov_value_model` parameter to the concrete class inheriting AbstractLOVValue
        and `lov_entity_model` to the model entity which is associated with both LOV concrete classes.

        For instance:

            class ConcreteLOVValue(AbstractLOVValue):
                lov_entity_model = SomeModel
                # or `lov_entity_model = "myapp.SomeModel"`

            class ConcreteLOVSelection(AbstractLOVSelection):
                lov_value_model = ConcreteLOVValue
                # or `lov_value_model = "myapp.ConcreteLOVValue"`

                lov_entity_model = SomeModel
                # or `lov_entity_model = "myapp.SomeModel"`
    """

    def __new__(cls, name, bases, attrs, **kwargs):
        model = super().__new__(cls, name, bases, attrs, **kwargs)

        for base in bases:
            if base.__name__ == "AbstractLOVSelection":
                ConcreteLOVSelectionModel = model

                if (
                    not ConcreteLOVSelectionModel._meta.abstract
                    and ConcreteLOVSelectionModel.lov_value_model is not None
                ):
                    if isinstance(ConcreteLOVSelectionModel.lov_value_model, str):
                        # Parse string representation of the target entity model class
                        try:
                            app_label, model_name = ConcreteLOVSelectionModel.lov_value_model.split(".")
                        except ValueError as e:
                            raise ModelClassParsingError(e)
                        ConcreteLOVSelectionModel.lov_value_model = apps.get_model(
                            app_label, model_name, require_ready=False
                        )

                    ConcreteLOVSelectionModel.add_to_class(
                        "lov_value",
                        models.ForeignKey(
                            ConcreteLOVSelectionModel.lov_value_model,
                            on_delete=ConcreteLOVSelectionModel.lov_value_on_delete,
                            related_name=ConcreteLOVSelectionModel.lov_value_model_related_name,
                            related_query_name=ConcreteLOVSelectionModel.lov_value_model_related_query_name,
                            blank=True,
                            null=True,
                        ),
                    )
                else:
                    raise IncorrectSubclassError("lov_value_model must be specified for concrete subclasses of AbstractLOVValue")

        return model


class LOVValueQuerySet(models.QuerySet):
    """
    Custom QuerySet for LOVValue models
    """

    def all(self):
        return self.none()

    def delete(self):
        return self.none()

    def for_entity(self, entity):
        """
        Returns all available values for a given entity, including:
        - all required default values
        - all non-required default values
        - all entity-specific values for this entity
        """
        return self.model.objects.filter(
            Q(value_type=LOVValueType.MANDATORY)
            | Q(value_type=LOVValueType.OPTIONAL)
            | Q(value_type=LOVValueType.CUSTOM, lov_entity=entity)
        )


class LOVValueManager(models.Manager):
    """
    Custom Manager for LOVValue models
    """

    def get_queryset(self):
        return super().get_queryset().filter(deleted__isnull=True)

    def create_for_entity(self, entity, name: str):
        """Provided an entity and a value name, creates the new value for that entity"""
        self.create(lov_entity=entity, name=name, value_type=LOVValueType.CUSTOM)

    def create_mandatory(self, name: str):
        """Provided a value name, creates the new value (selected for all entities)"""
        self.create(name=name, value_type=LOVValueType.MANDATORY)

    def create_optional(self, name: str):
        """Provided a value name, creates the new optional value (selectable by all entities)"""
        self.create(name=name, value_type=LOVValueType.OPTIONAL)

    def _create_default_option(self, item_name, item_values_dict=dict):
        """
        It should not be necessary, but this method can be overridden in a subclassed Manager
          if you need to modify how subclassed concrete instances are created.
        """

        # If value_type key is present, validate that it is LOVValueType.MANDATORY or LOVValueType.OPTIONAL
        #    LOVValueType.CUSTOM cannot be used in defaults
        for key, value in item_values_dict().items():
            if key == "value_type" and not (value == LOVValueType.MANDATORY or value == LOVValueType.OPTIONAL):
                raise Exception(
                    f"LOVValue defaults must be of type `LOVValueType.MANDATORY` or `LOVValueType.OPTIONAL`. "
                    f"For {item_name} you specified {key} = {value}."
                )

        obj, created = self.model.objects.update_or_create(
            name=item_name,
            defaults=item_values_dict,
        )

    def _import_defaults(self):
        """
        Get the default values from `Model.objects.defaults` and then create instances
           if they do not already exist or update if values have changed.

        Example:
            lov_defaults = {
                "Cereal_and_Grass": {"value_type": LOVValueType.MANDATORY},              # Creates a mandatory instance
                "Cereal_and_Grass__Alfalfa_Hay": {},                                      # Creates a mandatory instance
                "Cereal_and_Grass__Alfalfa_Seed": {"value_type": LOVValueType.OPTIONAL}, # Creates an optional instance
            }

        Note, it is not necessary to specify `{"value_type": LOVValueType.MANDATORY}` since options are
            mandatory by default. You could set the dict to `{}` and the value model instance will be
            set to mandatory.

        """
        for item_name, item_values_dict in self.model.lov_defaults.items():
            self.model.objects._create_default_option(item_name, item_values_dict)


class AbstractLOVValue(models.Model, metaclass=LOVValueModelBase):
    """
    Abstract model for defining all available List of Value options.

    Options which are provided by default through model configuration may be Mandatory or Optional

    Using `instance.delete()` only soft-deletes the option
    """

    lov_defaults = {}

    lov_entity_model = None
    lov_entity_on_delete = models.CASCADE
    lov_entity_model_related_name = "%(app_label)s_%(class)s_related"
    lov_entity_model_related_query_name = "%(app_label)s_%(class)ss"

    lov_selections_model = None

    lov_associated_entities_related_name = "%(app_label)s_%(class)s_selections"
    lov_associated_entities_related_query_name = "%(app_label)s_%(class)ss_selected"

    value_type = models.CharField(
        _("Option Type"),
        choices=LOVValueType.choices,
        default=LOVValueType.OPTIONAL,
        max_length=10,
        blank=True,
    )

    name = models.CharField(_("Value Name"), max_length=100)
    deleted = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When was this value deleted?"),
    )

    CombinedLOVValueManager = LOVValueManager.from_queryset(LOVValueQuerySet)
    objects = CombinedLOVValueManager()

    class Meta:
        verbose_name = _("List of Values Option")
        verbose_name_plural = _("List of Values Options")
        constraints = [
            UniqueConstraint(
                Lower("name").desc(),
                "lov_entity",
                name="%(app_label)s_%(class)s_name_val",
            ),
        ]
        abstract = True

    def delete(self, using=None, keep_parents=False, override=False):
        """
        Soft-delete options to prevent referencing an option that no longer exists
        """
        if self.value_type == OptionType.CUSTOM or override:
            self.deleted = timezone.now()
            self.save()

    def __str__(self):
        return self.name

    @classmethod
    def get_concrete_subclasses(cls):
        """
        Return a list of model classes which are subclassed from AbstractLOVValue and 
            are not themselves Abstract
        """
        result = []
        for model in apps.get_models():
            if issubclass(model, cls) and model is not cls and not model._meta.abstract:
                result.append(model)
        return result


class LOVSelectionQuerySet(models.QuerySet):
    """
    Custom QuerySet for LOVSelection models
    """


class LOVSelectionManager(models.Manager):
    """
    Custom Manager for LOVSelection models
    """

    def get_queryset(self):
        return super().get_queryset()

    def values_for_entity(self, entity):
        """
        Returns a QuerySet of the AbstractLOVValue subclassed model with all *available*
          values for a given entity, including:
          
        - all required default values
        - all non-required default values
        - all entity-specific values
        """
        return self.model.lov_value.rel.model.objects.for_entity(entity=entity)

    def selections_for_entity(self, entity):
        """
        Returns a QuerySet of the AbstractLOVValue subclassed model with all *selected*
          values for a given entity, including:
          
        - all required default values
        - all selected non-required default values
        - all selected entity-specific values
        """
        optional = {
            "value_type": LOVValueType.OPTIONAL,
            self.model.lov_value.rel.related_query_name + "__lov_entity": entity,
        }
        print(f"optional: {optional}")

        custom = {
            "value_type": LOVValueType.CUSTOM,
            self.model.lov_value.rel.related_query_name + "__lov_entity": entity,
        }
        print(f"custom: {custom}")

        return self.model.lov_value.rel.model.objects.filter(
            Q(value_type=LOVValueType.MANDATORY) | Q(**optional) | Q(**custom)
        )


class AbstractLOVSelection(models.Model, metaclass=LOVSelectionModelBase):
    """
    Identifies all selected LOV Values for a given entity, which it's users can then choose from

    A single entity can select multiple LOV Options
    """

    lov_entity_model = None
    lov_entity_on_delete = models.CASCADE
    lov_entity_model_related_name = "%(app_label)s_%(class)s_related"
    lov_entity_model_related_query_name = "%(app_label)s_%(class)ss"

    lov_value_model = None
    lov_value_on_delete = models.CASCADE
    lov_value_model_related_name = "%(app_label)s_%(class)s_related"
    lov_value_model_related_query_name = "%(app_label)s_%(class)ss"

    CombinedLOVSelectionManager = LOVSelectionManager.from_queryset(LOVSelectionQuerySet)
    objects = CombinedLOVSelectionManager()

    class Meta:
        verbose_name = _("List of Values Selection")
        verbose_name_plural = _("List of Values Selections")
        constraints = [
            UniqueConstraint(
                "lov_entity",
                "lov_value",
                name="%(app_label)s_%(class)s_name_val",
            ),
        ]
        abstract = True


