import Card from "@material-ui/core/Card";
import { withStyles } from "@material-ui/core/styles";
// import Container from "../../../components/Container";
import * as React from "react";
import CardTitle from "../../../components/CardTitle";
// import PageHeader from "../../../components/PageHeader";
import i18n from "../../../i18n";
// import CardSpacer from "../../../components/CardSpacer";
import HomeProductList from "./HomeProductList";

interface MoneyType {
  amount: number;
  currency: string;
}
interface HomeProductListCardProps {
  disabled: boolean;
  topProducts: Array<{
    id: string;
    name: string;
    orders: number;
    price: MoneyType;
    thumbnailUrl: string;
    variant: string;
  }>;
  onRowClick: (id: string) => () => void;
}

const decorate = withStyles({});
const HomeProductListCard = decorate<HomeProductListCardProps>(
  ({ topProducts, onRowClick }) => {
    return (
      <Card>
        <CardTitle title={i18n.t("Top products")} />
        <HomeProductList
          disabled={false}
          topProducts={topProducts}
          onRowClick={onRowClick}
        />
      </Card>
    );
  }
);
export default HomeProductListCard;
