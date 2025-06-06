from pydantic import BaseModel
from pydantic import Field
from typing import Optional

class TenderData(BaseModel):
    """
    Represents the structured data for a tender, based on the `answers_json` schema.
    Each field corresponds to a query in the tender documentation.
    """
    procurement_name: Optional[str] = Field(description="Наименование закупки (Поставляемая продукция или услуга)", default="")
    customer_info_company_name: Optional[str] = Field(description="Информация о заказчике или покупателе (Наименование компании)", default="")
    notice_number: Optional[str] = Field(description="Номер извещения", default="")
    publication_and_submission_deadline: Optional[str] = Field(description="Дата когда вышла закупка и срок окончания подачи: дата и время по мск?", default="")
    lot_names: Optional[str] = Field(description="Наименование лотов", default="")
    delivery_department: Optional[str] = Field(description="Подразделение, куда идет поставка", default="")
    initial_max_price_with_vat: Optional[str] = Field(description="Начальная максимальная цена с НДС", default="")
    contact_persons: Optional[str] = Field(description="Контактные лица (ФИО, номер телефона, e-mail, должность)", default="")
    application_security: Optional[str] = Field(description="Обеспечение заявки", default="")
    re_bidding_date: Optional[str] = Field(description="Дата переторжки", default="")
    etp_platform: Optional[str] = Field(description="На какой ЭТП (электронной торговой площадке) размещена закупка?", default="")
    application_review_deadline: Optional[str] = Field(description="Дата и время окончания рассмотрения заявок", default="")
    results_summary_date: Optional[str] = Field(description="Дата подведения итогов", default="")
    contract_security: Optional[str] = Field(description="Обеспечение договора", default="")
    participation_price: Optional[str] = Field(description="Цена участия в закупке", default="")
    warranty_requirements: Optional[str] = Field(description="Требования к гарантийным условиям товара", default="")
    required_delivery_period: Optional[str] = Field(description="Требуемый срок поставки товара", default="")
    payment_terms: Optional[str] = Field(description="Условия оплаты", default="")
    delivery_documents_names: Optional[str] = Field(description="Наименование документов для осуществления поставки", default="")
    delivery_method: Optional[str] = Field(description="Как будет осуществляться доставка?", default="")
    product_dimensions: Optional[str] = Field(description="Габаритные размеры товара", default="")
    product_purpose: Optional[str] = Field(description="Назначение товара", default="")
    contract_term: Optional[str] = Field(description="Срок действия договора", default="")
    delivery_address: Optional[str] = Field(description="Адрес доставки", default="")