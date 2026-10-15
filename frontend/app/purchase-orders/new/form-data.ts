export type PurchaseOrderPayload = {
  po_number: string;
  customer: string;
  po_date?: string;
  requested_delivery_date?: string;
  currency?: string;
  items: Array<{
    sku: string;
    description?: string;
    quantity: number;
    unit_price: number;
    line_total?: number;
    decoration_requirements?: string[];
  }>;
  ship_to: string;
  subtotal?: number;
  discount?: number;
  tax?: number;
  freight?: number;
  total?: number;
};

function requiredText(formData: FormData, name: string) {
  const value = formData.get(name);
  return typeof value === "string" ? value.trim() : "";
}

function optionalNumber(formData: FormData, name: string) {
  const text = requiredText(formData, name);
  if (!text) return undefined;
  const value = Number(text);
  return Number.isFinite(value) && value >= 0 ? value : null;
}

export function parsePurchaseOrderForm(formData: FormData): {
  purchaseOrder: PurchaseOrderPayload | null;
  error: string | null;
} {
  const poNumber = requiredText(formData, "po_number");
  const customer = requiredText(formData, "customer");
  const shipTo = requiredText(formData, "ship_to");
  const poDate = requiredText(formData, "po_date");
  const requestedDeliveryDate = requiredText(formData, "requested_delivery_date");
  const currency = requiredText(formData, "currency").toUpperCase();
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
    const description = requiredText(formData, `items.${index}.description`);
    const lineTotal = optionalNumber(formData, `items.${index}.line_total`);
    const decorations = requiredText(
      formData,
      `items.${index}.decoration_requirements`,
    )
      .split("\n")
      .map((value) => value.trim())
      .filter(Boolean);

    if (
      !sku ||
      !quantityText ||
      !priceText ||
      !Number.isInteger(quantity) ||
      quantity <= 0 ||
      !Number.isFinite(unitPrice) ||
      unitPrice < 0 ||
      lineTotal === null
    ) {
      return {
        purchaseOrder: null,
        error: "Correct all item SKUs, quantities, and prices.",
      };
    }

    items.push({
      sku,
      quantity,
      unit_price: unitPrice,
      ...(description ? { description } : {}),
      ...(lineTotal !== undefined ? { line_total: lineTotal } : {}),
      ...(decorations.length > 0 ? { decoration_requirements: decorations } : {}),
    });
  }

  const totals = {
    subtotal: optionalNumber(formData, "subtotal"),
    discount: optionalNumber(formData, "discount"),
    tax: optionalNumber(formData, "tax"),
    freight: optionalNumber(formData, "freight"),
    total: optionalNumber(formData, "total"),
  };

  if (Object.values(totals).some((value) => value === null)) {
    return { purchaseOrder: null, error: "Correct the financial totals." };
  }

  return {
    purchaseOrder: {
      po_number: poNumber,
      customer,
      ...(poDate ? { po_date: poDate } : {}),
      ...(requestedDeliveryDate ? { requested_delivery_date: requestedDeliveryDate } : {}),
      ...(currency ? { currency } : {}),
      items,
      ship_to: shipTo,
      ...Object.fromEntries(
        Object.entries(totals).filter(([, value]) => value !== undefined),
      ),
    },
    error: null,
  };
}
