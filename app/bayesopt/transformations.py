from baybe import transformations

from app.models.enums import TargetTransformation


def get_transformation(transformation_type: str) -> transformations.Transformation:
    """Get the corresponding BayBE transformation for a given TargetTransformation."""
    if transformation_type == TargetTransformation.LINEAR.value:
        return transformations.IdentityTransformation()
    elif transformation_type == TargetTransformation.BELL.value:
        return transformations.BellTransformation()
    elif transformation_type == TargetTransformation.TRIANGULAR.value:
        return transformations.TriangularTransformation()
    elif transformation_type == TargetTransformation.LOGARITHMIC.value:
        return transformations.LogarithmicTransformation()
    elif transformation_type == TargetTransformation.NONE.value:
        return None
    else:
        raise ValueError(f"Unsupported transformation type: {transformation_type}")
