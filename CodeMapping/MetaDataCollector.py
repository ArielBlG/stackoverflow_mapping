import pyecore.ecore as Ecore
from pyecore.resources import ResourceSet, URI, global_registry

global_registry[Ecore.nsURI] = Ecore  # We load the Ecore metamodel first
rset = ResourceSet()


class MetaModel:

    def __init(self, tasks_dict):
        self.tasks_dict = tasks_dict
        self.current_model = []

    def create_class_element(self, current_class, super_class):
        class_A = Ecore.EClass(current_class.class_name, superclass=super_class)
        self.current_model.append(class_A)

    def create_meta_model(self):
        # for query in self.tasks_dict.keys():
        #     query_element = Ecore.EPackage(query, abstract=True)
        #     for sub_class in self.tasks_dict[query]:
        #         self.create_class_element(sub_class, query_element)

        # We create each metaclass instance and we add their features
        NamedElement = Ecore.EClass('Query', abstract=True)
        # NamedElement.eStructuralFeatures.append(Ecore.EAttribute('Query', Ecore.EString))

        class_A = Ecore.EClass('Class A', superclass=NamedElement)
        Func_1A = Ecore.EClass('Func_1-A', superclass=class_A)
        class_A.eStructuralFeatures.append(Ecore.EReference('source', Func_1A, upper=-1, containment=True))
        # class_A.eStructuralFeatures.append(Ecore.EReference('source', Func_1A, upper=-1, containment=True))
        Func_2A = Ecore.EClass('Func_2-A', superclass=class_A)
        class_A.eStructuralFeatures.append(Ecore.EReference('source', Func_2A, upper=-1, containment=True))


        # Func_1A = Ecore.EModelElement('Func_1-A', )

        # class_B.eStructuralFeatures.append(Ecore.EReference('implement', class_A, upper=-1))
        # class_B.eSuperTypes.append(class_A)
        # class_B.eSuperTypes.append(Ecore.EReference('source', class_A, upper=-1))


        class_C = Ecore.EClass('Class C', superclass=NamedElement)
        Func_1C = Ecore.EClass('R.Func_1-C', superclass=class_C)
        class_C.eStructuralFeatures.append(Ecore.EReference('source', Func_1C, upper=-1, containment=True))

        # class_B = Ecore.EClass('Class B', superclass={NamedElement, class_A, class_C})
        class_B = Ecore.EClass('Class B', superclass=(NamedElement, class_A))
        # class_B.eSuperTypes.append(class_C)


        Func_1B = Ecore.EClass('Func_1-B', superclass=class_B)
        class_B.eStructuralFeatures.append(Ecore.EReference('source', Func_1B, upper=-1, containment=True))

        Func_2B = Ecore.EClass('Func_2-B', superclass=class_B)
        class_B.eStructuralFeatures.append(Ecore.EReference('source', Func_2B, upper=-1, containment=True))

        Func_2B.eStructuralFeatures.append(Ecore.EReference('source', Func_1C, upper=-1, containment=True))




        # Node = Ecore.EClass('Node', superclass=NamedElement)
        # Node.eStructuralFeatures.append(Ecore.EReference('references', Node, upper=-1))
        # Node.eStructuralFeatures.append(
        #     Ecore.EReference('relatives', Node, upper=-1, eOpposite=Node.eStructuralFeatures[0]))  # all on a single line

        # Graph.eStructuralFeatures.append(Ecore.EReference('graph', Node, upper=-1, containment=True))

        # At this point, you can already handle mode instances,
        # but we will define the container of all these elements
        GraphMetamodel = Ecore.EPackage('test', nsURI='http://sample/1.0', nsPrefix='test')
        GraphMetamodel.eClassifiers.extend([NamedElement, class_A, class_B, class_C, Func_1A, Func_2A, Func_1B, Func_2B, Func_1C, ])
        # rset.metamodel_registry[graphMMRoot.nsURI] = Ecore.graphMMRoot
        g2_resource = rset.create_resource(URI('./code_test.xmi'))
        g2_resource.append(GraphMetamodel)
        g2_resource.save()
        # That's it, you can create an instance of your Graph as seen on the previous section
        # g = Graph()
        # print(g)
