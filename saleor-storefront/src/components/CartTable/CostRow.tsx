import * as React from "react";

const CostRow: React.FC<{
  mediumScreen: boolean;
  heading: string;
  cost: string;
}> = ({ mediumScreen, heading, cost }) => (
  <tr>
    <td colSpan={mediumScreen ? 4 : 3} className="cart-table__cost">
      {heading}
    </td>
    <td colSpan={2}>{cost}</td>
  </tr>
);

export default CostRow;
