from framework.class_builder import CombinatorialClassBuilder
from framework.evaluation_oracle import EvaluationOracle
from framework.generic_samplers import *
from framework.decomposition_grammar import DecompositionGrammar, AliasSampler
from framework.generic_samplers import BoltzmannSamplerBase
from framework.utils import Counter

from planar_graph_sampler.combinatorial_classes.halfedge import HalfEdge
from planar_graph_sampler.combinatorial_classes.two_connected_graph import EdgeRootedTwoConnectedPlanarGraph, \
    TwoConnectedPlanarGraph
from planar_graph_sampler.evaluations_planar_graph import planar_graph_evals_n100
from planar_graph_sampler.grammar.network_decomposition import network_grammar


class ZeroAtomGraphBuilder(CombinatorialClassBuilder):
    def __init__(self):
        self.counter = Counter()

    def zero_atom(self):
        root_half_edge = HalfEdge(self_consistent=True)
        root_half_edge.node_nr = next(self.counter)
        root_half_edge_opposite = HalfEdge(self_consistent=True)
        root_half_edge_opposite.node_nr = next(self.counter)
        root_half_edge.opposite = root_half_edge_opposite
        root_half_edge_opposite.opposite = root_half_edge
        return EdgeRootedTwoConnectedPlanarGraph(root_half_edge)


def to_u_derived_class(obj):
    return UDerivedClass(obj)


def to_G_2(decomp):
    return TwoConnectedPlanarGraph(decomp.second.half_edge)


def to_G_2_dx(decomp):
    g = decomp.second
    assert isinstance(g, EdgeRootedTwoConnectedPlanarGraph) or isinstance(g, LDerivedClass)
    if isinstance(g, LDerivedClass):
        g = g.base_class_object
    return LDerivedClass(TwoConnectedPlanarGraph(g.half_edge))


def to_G_2_arrow(network):
    return EdgeRootedTwoConnectedPlanarGraph(network.half_edge)


def to_G_2_arrow_dx(network):
    return LDerivedClass(EdgeRootedTwoConnectedPlanarGraph(network.half_edge))


def change_deriv_order(obj):
    return obj.invert_derivation_order()


def divide_by_1_plus_y(evl, x, y):
    return evl / (1 + BoltzmannSamplerBase.oracle.get(y))


def divide_by_2(evl, x, y):
    return 0.5 * evl


def two_connected_graph_grammar():
    """Constructs the grammar for two connected planar graphs.

    Returns
    -------
    DecompositionGrammar
        The grammar for sampling from G_2_dx and G_2_dx_dx.
    """

    Z = ZeroAtomSampler
    L = LAtomSampler
    D = AliasSampler('D')
    D_dx = AliasSampler('D_dx')
    F = AliasSampler('F')
    F_dx = AliasSampler('F_dx')
    G_2_dy = AliasSampler('G_2_dy')
    # G_2_dy_dx = AliasSampler('G_2_dy_dx')
    G_2_dx_dy = AliasSampler('G_2_dx_dy')
    G_2_arrow = AliasSampler('G_2_arrow')
    G_2_arrow_dx = AliasSampler('G_2_arrow_dx')
    Trans = TransformationSampler
    Bij = BijectionSampler
    DxFromDy = LDerFromUDerSampler

    grammar = DecompositionGrammar()
    grammar.rules = network_grammar().rules

    grammar.rules = {

        # two connected

        'G_2_arrow': Trans(Z() + D, to_G_2_arrow, eval_transform=divide_by_1_plus_y),  # see 5.5

        'F': Bij(L() ** 2 * G_2_arrow, to_G_2),

        'G_2_dy': Trans(F, to_u_derived_class, eval_transform=divide_by_2),

        'G_2_dx': DxFromDy(G_2_dy, alpha_l_u=2.0),  # see p. 26

        # l-derived two connected

        'G_2_arrow_dx': Trans(D_dx, to_G_2_arrow_dx, eval_transform=divide_by_1_plus_y),

        'F_dx': Bij(L() ** 2 * G_2_arrow_dx + 2 * L() * G_2_arrow, to_G_2_dx),

        'G_2_dx_dy': Trans(F_dx, to_u_derived_class, eval_transform=divide_by_2),

        # 'G_2_dy_dx': Bij(G_2_dx_dy, change_deriv_order),

        'G_2_dx_dx': DxFromDy(G_2_dx_dy, alpha_l_u=1.0),  # see 5.5

    }
    grammar.set_builder(['G_2_arrow'], ZeroAtomGraphBuilder())
    return grammar


if __name__ == '__main__':
    grammar = two_connected_graph_grammar()
    grammar.init()

    BoltzmannSamplerBase.oracle = EvaluationOracle(planar_graph_evals_n100)
    BoltzmannSamplerBase.debug_mode = True

    symbolic_x = 'x*G_1_dx(x,y)'
    symbolic_y = 'y'

    sampled_class = 'G_2_dx_dx'

    while True:
        try:
            g = grammar.sample(sampled_class, symbolic_x, symbolic_y)
        except RecursionError:
            pass
        if g.u_size > 5:
            if isinstance(g, DerivedClass):
                g = g.base_class_object
            if isinstance(g, DerivedClass):
                g = g.base_class_object
            assert g.is_consistent
            print(g)

            import matplotlib.pyplot as plt

            g.plot(with_labels=False, node_size=25, use_planar_drawer=True)
            plt.show()
