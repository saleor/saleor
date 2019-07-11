import { smallScreen } from "../../globalStyles/scss/variables.scss";
import "./scss/index.scss";

import * as React from "react";
import Media from "react-media";

import CostRow from "./CostRow";
import ProductRow, { EditableProductRowProps, LineI } from "./ProductRow";

interface TableProps extends EditableProductRowProps {
  lines: LineI[];
  subtotal: string;
  deliveryCost?: string;
  totalCost?: string;
}

const Table: React.FC<TableProps> = ({
  subtotal,
  deliveryCost,
  totalCost,
  lines,
  ...rowProps
}) => (
  <Media query={{ minWidth: smallScreen }}>
    {mediumScreen => (
      <table className="cart-table">
        <thead>
          <tr>
            <th>Products</th>
            {mediumScreen && <th>Price</th>}
            <th>Size</th>
            <th className="cart-table__quantity-header">Quantity</th>
            <th colSpan={2}>{mediumScreen ? "Total Price" : "Price"}</th>
          </tr>
        </thead>
        <tbody>
          {lines.map(line => (
            <ProductRow
              key={line.id}
              line={line}
              mediumScreen={mediumScreen}
              {...rowProps}
            />
          ))}
        </tbody>
        <tfoot>
          <CostRow
            mediumScreen={mediumScreen}
            heading="Subtotal"
            cost={subtotal}
          />
          {deliveryCost && (
            <CostRow
              mediumScreen={mediumScreen}
              heading="Delivery Cost"
              cost={deliveryCost}
            />
          )}
          {totalCost && (
            <CostRow
              mediumScreen={mediumScreen}
              heading="Total Cost"
              cost={totalCost}
            />
          )}
        </tfoot>
      </table>
    )}
  </Media>
);

export default Table;
