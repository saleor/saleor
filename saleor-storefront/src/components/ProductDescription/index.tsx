import "./scss/index.scss";

import * as React from "react";

import { SelectField, TextField } from "..";
import {
  ProductPriceInterface,
  ProductVariantInterface
} from "../../core/types";
import { maybe } from "../../core/utils";
import { CartContext, CartLine } from "../CartProvider/context";
import { SelectValue } from "../SelectField";
import AddToCart from "./AddToCart";

interface ProductDescriptionProps {
  productVariants: ProductVariantInterface[];
  name: string;
  children: React.ReactNode;
  addToCart(varinatId: string, quantity?: number): void;
}

interface ProductDescriptionState {
  primaryPicker?: { label: string; values: string[]; selected?: string };
  secondaryPicker?: { label: string; values: string[]; selected?: string };
  quantity: number;
  variants: { [x: string]: string[] };
  variant: string;
  variantStock: number;
  price: ProductPriceInterface;
}

class ProductDescription extends React.Component<
  ProductDescriptionProps,
  ProductDescriptionState
> {
  constructor(props: ProductDescriptionProps) {
    super(props);
    const pickers =
      maybe(() => this.props.productVariants[0].attributes[0].attribute) &&
      this.createPickers();
    this.state = {
      ...pickers,
      price: this.props.productVariants[0].price,
      quantity: 1,
      variant: "",
      variantStock: null,
    };
  }

  componentDidMount() {
    this.getVariant();
  }

  createPickers = () => {
    const primaryPicker = {
      label: this.props.productVariants[0].attributes[0].attribute.name,
      selected: "",
      values: [],
    };

    let secondaryPicker;

    if (this.props.productVariants[0].attributes.length > 1) {
      secondaryPicker = {
        label: this.props.productVariants[0].attributes
          .slice(1)
          .map(attribute => attribute.attribute.name)
          .join(" / "),
        selected: "",
        values: [],
      };
    }

    const variants = {};

    this.props.productVariants.map(variant => {
      if (!primaryPicker.values.includes(variant.attributes[0].value.value)) {
        primaryPicker.values.push(variant.attributes[0].value.value);
      }

      if (secondaryPicker) {
        const combinedValues = variant.attributes
          .slice(1)
          .map(attribute => attribute.value.value)
          .join(" / ");

        if (!secondaryPicker.values.includes(combinedValues)) {
          secondaryPicker.values.push(combinedValues);
        }

        if (variants[variant.attributes[0].value.value]) {
          variants[variant.attributes[0].value.value] = [
            ...variants[variant.attributes[0].value.value],
            combinedValues,
          ];
        } else {
          variants[variant.attributes[0].value.value] = [combinedValues];
        }
      }

      primaryPicker.selected = primaryPicker.values[0];
      if (secondaryPicker) {
        secondaryPicker.selected = secondaryPicker.values[0];
      }
    });

    return {
      primaryPicker,
      secondaryPicker,
      variants,
    };
  };

  onPrimaryPickerChange = value => {
    const primaryPicker = this.state.primaryPicker;
    primaryPicker.selected = value;
    this.setState({ primaryPicker });
    if (this.state.secondaryPicker) {
      if (
        !this.state.variants[value].includes(
          this.state.secondaryPicker.selected
        )
      ) {
        this.onSecondaryPickerChange("");
        this.setState({ variant: "" });
      } else {
        this.getVariant();
      }
    } else {
      this.getVariant();
    }
  };

  onSecondaryPickerChange = value => {
    const secondaryPicker = this.state.secondaryPicker;
    secondaryPicker.selected = value;
    this.setState({ secondaryPicker });
    this.getVariant();
  };

  getVariant = () => {
    const { productVariants } = this.props;
    const { primaryPicker, secondaryPicker } = this.state;
    let variant;

    if (!secondaryPicker && primaryPicker) {
      variant = productVariants.find(
        variant => variant.name === `${primaryPicker.selected}`
      );
    } else if (secondaryPicker && primaryPicker) {
      variant = productVariants.find(
        variant =>
          variant.name ===
          `${primaryPicker.selected} / ${secondaryPicker.selected}`
      );
    } else {
      variant = this.props.productVariants[0];
    }

    const variantStock = variant.stockQuantity;
    const price = variant.price;
    this.setState({ variant: variant.id, variantStock, price });
  };

  handleSubmit = () => {
    this.props.addToCart(this.state.variant, this.state.quantity);
  };

  canAddToCart = (lines: CartLine[]) => {
    const { variant, quantity, variantStock } = this.state;
    const cartLine = lines.find(({ variantId }) => variantId === variant);
    const syncedQuantityWithCart = cartLine
      ? quantity + cartLine.quantity
      : quantity;
    return (
      quantity !== 0 && (variant && variantStock >= syncedQuantityWithCart)
    );
  };

  render() {
    const { children, name } = this.props;
    const {
      price,
      primaryPicker,
      quantity,
      secondaryPicker,
      variants,
    } = this.state;

    return (
      <div className="product-description">
        <h3>{name}</h3>
        <h4>{price.localized}</h4>
        <div className="product-description__variant-picker">
          {primaryPicker && (
            <SelectField
              onChange={(e: SelectValue) => this.onPrimaryPickerChange(e.value)}
              label={primaryPicker.label}
              key={primaryPicker.label}
              value={{
                label: primaryPicker.selected,
                value: primaryPicker.selected,
              }}
              styleType="grey"
              options={primaryPicker.values.map(value => ({
                label: value,
                value,
              }))}
            />
          )}
          {secondaryPicker && (
            <SelectField
              onChange={(e: SelectValue) =>
                this.onSecondaryPickerChange(e.value)
              }
              label={secondaryPicker.label}
              key={secondaryPicker.label}
              value={
                secondaryPicker.selected && {
                  label: secondaryPicker.selected,
                  value: secondaryPicker.selected,
                }
              }
              styleType="grey"
              options={secondaryPicker.values.map(value => ({
                isDisabled: !variants[primaryPicker.selected].includes(value),
                label: value,
                value,
              }))}
            />
          )}
          <TextField
            type="number"
            label="Quantity"
            min="1"
            value={quantity || ""}
            styleType="grey"
            onChange={e =>
              this.setState({ quantity: Math.max(1, Number(e.target.value)) })
            }
          />
        </div>
        <div className="product-description__about">
          <h4>Description</h4>
          {children}
        </div>
        <CartContext.Consumer>
          {({ lines }) => (
            <AddToCart
              onSubmit={this.handleSubmit}
              lines={lines}
              disabled={!this.canAddToCart(lines)}
            />
          )}
        </CartContext.Consumer>
      </div>
    );
  }
}

export default ProductDescription;
