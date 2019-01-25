import * as React from "react";

import Container from "../../../components/Container";
import Form from "../../../components/Form";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import { maybe } from "../../../misc";
import { ListProps } from "../../../types";
import { VoucherType } from "../../../types/globalTypes";
import { VoucherDetails_voucher } from "../../types/VoucherDetails";
import VoucherInfo from "../VoucherInfo";
import VoucherSummary from "../VoucherSummary";

export interface FormData {
  code: string;
  name: string;
  type: VoucherType;
}

export interface VoucherDetailsPageProps
  extends Pick<ListProps, Exclude<keyof ListProps, "onRowClick">> {
  defaultCurrency: string;
  voucher: VoucherDetails_voucher;
  onBack: () => void;
  onSubmit: (data: FormData) => void;
}

const VoucherDetailsPage: React.StatelessComponent<VoucherDetailsPageProps> = ({
  defaultCurrency,
  disabled,
  pageInfo,
  voucher,
  onBack,
  onNextPage,
  onPreviousPage,
  onSubmit
}) => {
  const initialForm: FormData = {
    code: maybe(() => voucher.code),
    name: maybe(() => voucher.name),
    type: maybe(() => voucher.type)
  };

  return (
    <Form initial={initialForm} onSubmit={onSubmit}>
      {({ change, data, errors, hasChanged, submit }) => (
        <Container width="md">
          <PageHeader title={maybe(() => voucher.name)} onBack={onBack} />
          <Grid>
            <div>
              <VoucherInfo data={data} disabled={disabled} onChange={change} />
            </div>
            <div>
              <VoucherSummary
                defaultCurrency={defaultCurrency}
                voucher={voucher}
              />
            </div>
          </Grid>
        </Container>
      )}
    </Form>
  );
};
VoucherDetailsPage.displayName = "VoucherDetailsPage";

export default VoucherDetailsPage;
