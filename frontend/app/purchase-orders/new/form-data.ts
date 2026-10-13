export type PurchaseOrderPayload = {
  po_number: string;
  customer: string;
  items: Array<{
    sku: string;
    quantity: number;
    unit_price: number;
  }>;
  ship_to: string;
};

function requiredText(formData: FormData, name: string) {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

export function parsePurchaseOrderForm(formData: FormData): {
  purchaseOrder: PurchaseOrderPayload | null;
  error: string | null;
} {
  const poNumber = requiredText(formData, "po_number");
  const customer = requiredText(formData, "customer");
  const shipTo = requiredText(formData, "ship_to");
  const itemCount = Number(formData.get("item_count"));

  if (!poNumber || !customer || !shipTo || !Number.isInteger(itemCount) || itemCount < 1) {
    return {
      purchaseOrder: null,
      error: "Complete every required field before continuing.",
    };
  }

  const items = [];

  for (let index = 0; index < itemCount; index += 1) {
    const sku = requiredText(formData, `items.${index}.sku`);
    const quantityText = requiredText(formData, `items.${index}.quantity`);
    const priceText = requiredText(formData, `items.${index}.unit_price`);
    const quantity = Number(quantityText);
    const unitPrice = Number(priceText);

    if (
      !sku ||
      !quantityText ||
      !priceText ||
      !Number.isInteger(quantity) ||
      quantity <= 0 ||
      !Number.isFinite(unitPrice) ||
      unitPrice < 0
    ) {
      return {
        purchaseOrder: null,
        error: "Correct all item SKUs, quantities, and prices.",
      };
    }

    items.push({ sku, quantity, unit_price: unitPrice });
  }

  return {
    purchaseOrder: {
      po_number: poNumber,
      customer,
      items,
      ship_to: shipTo,
    },
    error: null,
  };
}
