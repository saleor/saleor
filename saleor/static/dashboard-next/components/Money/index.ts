import Money from "./Money";

export { default } from "./Money";
export * from "./Money";

export function addMoney(init: Money, ...args: Money[]): Money {
  return {
    amount: args.reduce((acc, curr) => acc + curr.amount, init.amount),
    currency: init.currency
  };
}
export function subtractMoney(init: Money, ...args: Money[]): Money {
  return {
    amount: args.reduce((acc, curr) => acc - curr.amount, init.amount),
    currency: init.currency
  };
}
