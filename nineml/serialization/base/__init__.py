# The name of the attribute used to represent the "namespace" of the element in
# formats that don't support namespaces explicitly.
NS_ATTR = '@namespace'

# The name of the attribute used to represent the "body" of the element in
# formats that don't support element bodies.
# NB: Body elements should be phased out in later 9ML versions to avoid this.
BODY_ATTR = '@body'

from .visitors import BaseSerializer, BaseUnserializer  # @IgnorePep8
