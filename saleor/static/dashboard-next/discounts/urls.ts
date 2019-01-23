import * as urlJoin from "url-join";

export const discountSection = "/discounts/";

export const saleSection = urlJoin(discountSection, "sales");
export const saleListPath = saleSection;
export const saleListUrl = saleListPath;
export const salePath = (id: string) => urlJoin(saleSection, id);
export const saleUrl = (id: string) => salePath(encodeURIComponent(id));
export const saleAddPath = urlJoin(saleSection, "add");
export const saleAddUrl = saleAddPath;

export const voucherListPath = urlJoin(discountSection, "vouchers");
export const voucherListUrl = voucherListPath;
