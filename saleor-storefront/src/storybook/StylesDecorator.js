import * as React from "react";

import "./index.scss";

const StylesDecorator = storyFn => <div className="storybook">{storyFn()}</div>;

export default StylesDecorator;
