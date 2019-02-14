import * as urlJoin from "url-join";

export const discountSection = "/discounts/";

export const saleSection = urlJoin(discountSection, "sales");
export const saleListPath = saleSection;
export const saleListUrl = saleListPath;
export const salePath = (id: string) => urlJoin(saleSection, id);
export const saleUrl = (id: string) => salePath(encodeURIComponent(id));
export const saleAddPath = urlJoin(saleSection, "add");
export const saleAddUrl = saleAddPath;

export const voucherSection = urlJoin(discountSection, "vouchers");
export const voucherListPath = voucherSection;
export const voucherListUrl = voucherListPath;
export const voucherPath = (id: string) => urlJoin(voucherSection, id);
export const voucherUrl = (id: string) => voucherPath(encodeURIComponent(id));
export const voucherAddPath = urlJoin(voucherSection, "add");
export const voucherAddUrl = voucherAddPath;
