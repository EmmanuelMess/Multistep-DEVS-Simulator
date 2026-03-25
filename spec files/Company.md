# Company spec file

The folder design/DEVS diagrams/factories provides the diagrams for code/src/examples/factories; in the same vein,
taking the reference provided by design/DEVS diagrams/company/*, generate the source python for
code/src/examples/company. 

The provided DEVS modules have input and output ports that are not connected to Atomic models, those are for external
control. External control should be provided in main.py. Input interfaces provided should be: (1) Random inputs
(with distributions defined per element); (2) List of timestamped inputs. Output interface should be output to console
as in the reference.

## Company

### External interactions

Company receives requests from the outside, via `DemandProduct(Product(i))`, where `i` is the ith
product (either produced or not by the modeled company). It also receives products, `Product(i)`, which should be 
either primary goods or intermidiate goods required to produce the modeled company's products; it receives products 
after demanding them via `DemandProduct(Product(i))`. The modeled company offers its products
via `OfferProduct(Product(i))`, and it tries to keep on top of demand fluctuations (via keeping track
of `DemandProduct(Product(i)))` for all `Product(i)` that the company produces. 

In the simulation, to receive a product, the outside must request it via `DemandProduct(Product(i))` and then pay for
it via `Payment`. It can choose to demand an offered product or not. Offered products should imply that the offered 
product is in some sort of inventory, available "faster" for some definition of faster.

Outside the company there are employees, which are provided via `EmployeeOffering(Employee(i))`
and revoked (by the employee `i`) via `EmployeeResignation(Employee(i))` and requested by `LookingForEmployee`
and revoked (by the modeled company) via `FireEmployee(Employee(i))`. 

External investors provide capital to start to run the company via `Capital`, and under this model do not expect to be
repayed. 

### Administration

Inside the `Company`, the `Administration` Atomic keeps track of capital, payments, employees, and demanded (by the
other Atomics inside the modeled company) primary or intermidiate products. It should also take into account the
cost and need of improvements provided by R&D. And it should take into account employee demand (`RequestEmployee`)
by `Manufacturing` and `R&D` and use `EmployeeOffering` to cover these demands.

### Manufacturing

Inside the `Company`, the `Manufacturing` Atomic should request employees to manufacture products, taking into account
demand, and availability of primary or intermidiate products. It should also receive improvements to its production 
process, in the form of better efficiency (measured in time taken per unit product).

The bill of materials (and time cost) for each product is not specified, and should be provided as input to the
simulation. Along with which products and general costs are provided to the modeled company by the outside.

### R&D

Inside the `Company`, the `R&D` Atomic should request employees to produce improvements to the required production
processes, as the `Administration` demands them, via `StartImprovements`.

## Model limitations

- The payroll isn't modeled, the cost of employees is not modeled in terms of payroll, just in terms of unit scarcity.
- R&D modelling is very basic.
- Payments for products goes on the honor system, both for products from the world and products provided by the company.
- The company cannot go bankrupt, only have negative capital.

## Implementation details

- Names should be consistent with the spec, where possible
- Each event in the chart contains information to track relevant information, only some of the information is 
explicitly given (mainly `Employee(i)` and `Product(i)`). As an example of not given data in an event: `Capital`
constains the amount of capital, and an Id to track the capital event uniquely.
- The list of products is not specified, and should be provided as input to the simulation, the products can be primary,
intermediate or final, relative to the modeled company.
- Typing is not part of this spec.
- Employee availability is part of the parameters passed to the simulation
- Tracking of demand by the modeled company is not specified here and should be done a simple manner, as well as
tracking of improvements.
- Internal implementations of the Atomic components should be as simple as possible while following the prescriptions 
of this file.
- Halt production of the company if there is nothing that can be produced that creates profits: for example
if there is no demand and an excess of inventory (offerings not sold)
- Provide a showcase of all the functionality, as part of both the timestamped and random inputs mechanisms

## Math 

- It must be provable that there is no way to generate an infinite loop in the simulation such that
time stays still ($\delta t = 0$) but the same event occurs twice.

