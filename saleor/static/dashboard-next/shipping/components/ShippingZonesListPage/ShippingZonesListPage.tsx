import * as React from "react";

import AppHeader from "../../../components/AppHeader";
import Container from "../../../components/Container";
import Grid from "../../../components/Grid";
import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
import { PageListProps } from "../../../types";
import { WeightUnitsEnum } from "../../../types/globalTypes";
import { ShippingZoneFragment } from "../../types/ShippingZoneFragment";
import ShippingWeightUnitForm from "../ShippingWeightUnitForm";
import ShippingZonesList from "../ShippingZonesList";

export interface ShippingZonesListPageProps extends PageListProps {
  defaultWeightUnit: WeightUnitsEnum;
  shippingZones: ShippingZoneFragment[];
  onBack: () => void;
  onRemove: (id: string) => void;
  onSubmit: (unit: WeightUnitsEnum) => void;
}

const ShippingZonesListPage: React.StatelessComponent<
  ShippingZonesListPageProps
> = ({
  defaultWeightUnit,
  disabled,
  onAdd,
  onBack,
  onNextPage,
  onPreviousPage,
  onRemove,
  onRowClick,
  onSubmit,
  pageInfo,
  shippingZones
}) => (
  <Container>
    <AppHeader onBack={onBack}>{i18n.t("Configuration")}</AppHeader>
    <PageHeader
      title={i18n.t("Shipping", {
        context: "page header"
      })}
    />
    <Grid>
      <div>
        <ShippingZonesList
          disabled={disabled}
          onAdd={onAdd}
          onNextPage={onNextPage}
          onPreviousPage={onPreviousPage}
          onRemove={onRemove}
          onRowClick={onRowClick}
          pageInfo={pageInfo}
          shippingZones={shippingZones}
        />
      </div>
      <div>
        <ShippingWeightUnitForm
          defaultWeightUnit={defaultWeightUnit}
          disabled={disabled}
          onSubmit={onSubmit}
        />
      </div>
    </Grid>
  </Container>
);
ShippingZonesListPage.displayName = "ShippingZonesListPage";
export default ShippingZonesListPage;
