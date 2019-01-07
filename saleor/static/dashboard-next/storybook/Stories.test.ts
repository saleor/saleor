import createGenerateClassName from "@material-ui/core/styles/createGenerateClassName";
import initStoryshots from "@storybook/addon-storyshots";
import { configure, render } from "enzyme";
import * as Adapter from "enzyme-adapter-react-16";
import toJSON from "enzyme-to-json";

configure({ adapter: new Adapter() });

jest.mock("@material-ui/core/styles/createGenerateClassName");
(createGenerateClassName as any).mockImplementation(
  () => (rule, stylesheet) => {
    return [stylesheet.options.meta, rule.key, "id"].join("-");
  }
);

initStoryshots({
  configPath: "saleor/static/dashboard-next/storybook/",
  test({ story }) {
    const result = render((story as any).render());
    expect(toJSON(result)).toMatchSnapshot();
  }
});
