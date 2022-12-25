import trac193

bdv = trac193.Money._UseForTag('Value').elementBinding().typeDefinition()
rdv = trac193.OpenDeliveries._UseForTag('Value').elementBinding().typeDefinition()

assert issubclass(rdv, bdv)
