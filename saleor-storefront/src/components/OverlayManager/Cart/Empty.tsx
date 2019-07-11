import * as React from "react";

import { Button } from "../..";

const Empty: React.FC<{ overlayHide(): void }> = ({ overlayHide }) => (
  <div className="cart__empty">
    <h4>Yor bag is empty</h4>
    <p>
      You haven’t added anything to your bag. We’re sure you’ll find something
      in our store
    </p>
    <div className="cart__empty__action">
      <Button secondary onClick={overlayHide}>
        Continue Shopping
      </Button>
    </div>
  </div>
);

export default Empty;
