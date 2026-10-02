from fastapi import APIRouter
from backend.app.config import settings
from backend.app.schemas.schemas import WeightSettings, WeightSettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("/weights", response_model=WeightSettings)
def get_weights():
    return WeightSettings(
        weight_identity_mismatch=settings.WEIGHT_IDENTITY_MISMATCH,
        weight_document_issues=settings.WEIGHT_DOCUMENT_ISSUES,
        weight_registration_issues=settings.WEIGHT_REGISTRATION_ISSUES,
        weight_address_mismatch=settings.WEIGHT_ADDRESS_MISMATCH,
        weight_ml_anomaly=settings.WEIGHT_ML_ANOMALY,
        weight_missing_info=settings.WEIGHT_MISSING_INFO
    )

@router.put("/weights", response_model=WeightSettings)
def update_weights(weights_in: WeightSettingsUpdate):
    if weights_in.weight_identity_mismatch is not None:
        settings.WEIGHT_IDENTITY_MISMATCH = weights_in.weight_identity_mismatch
    if weights_in.weight_document_issues is not None:
        settings.WEIGHT_DOCUMENT_ISSUES = weights_in.weight_document_issues
    if weights_in.weight_registration_issues is not None:
        settings.WEIGHT_REGISTRATION_ISSUES = weights_in.weight_registration_issues
    if weights_in.weight_address_mismatch is not None:
        settings.WEIGHT_ADDRESS_MISMATCH = weights_in.weight_address_mismatch
    if weights_in.weight_ml_anomaly is not None:
        settings.WEIGHT_ML_ANOMALY = weights_in.weight_ml_anomaly
    if weights_in.weight_missing_info is not None:
        settings.WEIGHT_MISSING_INFO = weights_in.weight_missing_info

    return get_weights()
