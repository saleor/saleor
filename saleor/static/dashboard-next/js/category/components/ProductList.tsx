import * as React from "react";
import Grid from "material-ui/Grid";
import Typography from "material-ui/Typography";
import Button from "material-ui/Button";
import { Link } from "react-router-dom";

import { CategoryPropertiesQuery } from "../gql-types";
import { ProductChildElement } from "./ProductChildElement";
import { categoryAddUrl } from "../";
import i18n from "../../i18n";

interface ProductListProps {
  products: CategoryPropertiesQuery["category"]["products"]["edges"];
  loading: boolean;
  parentId: string;
  handleLoadMore();
  canLoadMore: boolean;
}

export const ProductList: React.StatelessComponent<ProductListProps> = ({
  products,
  loading,
  parentId,
  handleLoadMore,
  canLoadMore
}) => (
  <>
    <Typography variant="display1">
      {i18n.t("Products", { context: "title" })}
    </Typography>
    <Button
      color="primary"
      component={props => <Link to={"#"} {...props} />}
      disabled={loading}
    >
      {i18n.t("Add product", { context: "button" })}
    </Button>
    <Grid container>
      {loading ? (
        <ProductChildElement
          loading={true}
          label={""}
          url={""}
          price=""
          thumbnail=""
        />
      ) : (
        <>
          {products.length > 0 ? (
            <>
              {products.map(edge => (
                <ProductChildElement
                  url={"#"}
                  label={edge.node.name}
                  price={edge.node.price.grossLocalized}
                  thumbnail={edge.node.thumbnailUrl}
                  key={edge.node.id}
                />
              ))}
            </>
          ) : (
            <Typography variant="headline">
              {i18n.t("No products found")}
            </Typography>
          )}
        </>
      )}
    </Grid>
    {canLoadMore && (
      <Button color="primary" onClick={handleLoadMore}>
        {i18n.t("Load more", { context: "button" })}
      </Button>
    )}
  </>
);
